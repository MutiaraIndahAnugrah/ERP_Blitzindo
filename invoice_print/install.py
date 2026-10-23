"""Local-only replacement of the invoice print items block; no invoice saves."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlsplit
import base64

import frappe
from frappe.utils.jinja import get_jenv

FORMAT = 'PPN TEST'
SAMPLES = ['DPKK-0826-0002', 'PBU-0926-0021']
MARKER = 'blitz-dynamic-source-items-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def fingerprint():
    result = {}
    for dt, filters in [
        ('Sales Invoice', {'name':['in',SAMPLES]}),
        ('Sales Invoice Item', {'parent':['in',SAMPLES]}),
        ('Sales Taxes and Charges', {'parent':['in',SAMPLES]}),
        ('GL Entry', {'voucher_type':'Sales Invoice','voucher_no':['in',SAMPLES]}),
        ('Payment Entry Reference', {'reference_doctype':'Sales Invoice','reference_name':['in',SAMPLES]}),
    ]:
        rows = frappe.get_all(dt, filters=filters, fields=['*'], order_by='name')
        result[dt] = {'count':len(rows),'sha256':digest(rows)}
    return result


def prepare(format_doc, template):
    if format_doc.doc_type != 'Sales Invoice' or not format_doc.print_format_builder or format_doc.custom_format:
        raise RuntimeError('Expected the Sales Invoice Builder format PPN TEST. Nothing changed.')
    fields = json.loads(format_doc.format_data or '[]')
    matches = [i for i,f in enumerate(fields) if f.get('fieldname') == 'items' or MARKER in (f.get('options') or '')]
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one invoice items block; review the format before applying.')
    fields[matches[0]] = {'fieldname':'_custom_html','fieldtype':'HTML','print_hide':0,
                          'label':'','options':template}
    return json.dumps(fields,ensure_ascii=False)


def source_summary(invoice):
    groups=[]
    for item in invoice.items:
        link=item.get('detail_order')
        if not link and item.get('so_detail'):
            so=frappe.db.get_value('Sales Order Item',item.so_detail,['parent','detail_order'],as_dict=True)
            if so and so.parent==item.get('sales_order'):
                link=so.detail_order
        count=0
        if link and frappe.db.exists('Detail Order',link):
            source=frappe.get_doc('Detail Order',link)
            if source.has_permission('read'):
                count=len(source.get('details') or [])
        groups.append({'row':item.idx,'qty':item.qty,'amount':item.amount,'source_count':count})
    return groups


def check_rendered_groups(html, source_rows):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup(html,'html.parser')
    expected={r['row']:r for r in source_rows}
    seen=[];groups=[]
    for table in soup.select('.blitz-source-items table[data-blitz-item-rows]'):
        ids=[int(value) for value in table['data-blitz-item-rows'].split(',')]
        if any(i not in expected for i in ids):
            raise RuntimeError('Printed group references an unknown invoice item.')
        qty=float(table['data-blitz-billed-qty'])
        amount=float(table['data-blitz-billed-amount'])
        count=int(table['data-blitz-detail-count'])
        if abs(qty-sum(expected[i]['qty'] for i in ids))>0.000001 or count!=sum(expected[i]['source_count'] for i in ids) or abs(amount-sum(expected[i]['amount'] for i in ids))>0.005:
            raise RuntimeError('Grouping changed the original quantity, amount or source detail count.')
        seen.extend(ids);groups.append({'invoice_rows':ids,'qty':qty,'amount':amount,'source_count':count})
    if sorted(seen)!=sorted(expected):
        raise RuntimeError('Invoice items were lost or duplicated during print grouping.')
    return groups


def local_preview_images(html):
    """Keep missing restored-site images from breaking table-only PDF verification.

    Only the local preview is adjusted, never the saved format or Letter Head.
    """
    from bs4 import BeautifulSoup
    import requests
    soup=BeautifulSoup(html,'html.parser')
    missing=0
    for image in soup.find_all('img'):
        src=image.get('src') or ''
        if src.startswith('data:'):
            continue
        url=urljoin('http://127.0.0.1:8000',src)
        parts=urlsplit(url)
        content=None
        if parts.hostname in ['127.0.0.1','localhost','blitz.local']:
            url=parts._replace(netloc='127.0.0.1:8000').geturl()
            try:
                response=requests.get(url,timeout=10)
                if response.status_code==200 and response.headers.get('Content-Type','').startswith('image/'):
                    content=response
            except requests.RequestException:
                pass
        if content is not None:
            image['src']='data:'+content.headers['Content-Type'].split(';')[0]+';base64,'+base64.b64encode(content.content).decode()
        else:
            missing+=1
            image['src']='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=='
    return str(soup),missing


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true',help='Commit only the Print Format change after validation.')
    args=parser.parse_args()
    package=Path(__file__).resolve().parent
    template=(package/'items.html').read_text(encoding='utf8')
    frappe.init(site='blitz.local')
    frappe.connect()
    run_dir=None
    try:
        if frappe.local.site!='blitz.local':
            raise RuntimeError('This script is restricted to blitz.local.')
        from frappe.utils.scheduler import is_scheduler_disabled
        if not frappe.conf.get('mute_emails') or not is_scheduler_disabled() or frappe.db.count('Webhook'):
            raise RuntimeError('Local safeguards are not enabled. Nothing changed.')
        frappe.set_user('Administrator')
        # CLI has no incoming HTTP host. Resolve relative assets against the running
        # local bench; blitz.local is not necessarily registered in WSL DNS.
        # This is process-local and does not modify site_config or the Print Format.
        frappe.local.conf.host_name='http://127.0.0.1:8000'
        # Abort if the earlier form integration is still active.
        hooks=frappe.get_hooks('doc_events').get('Sales Invoice',{})
        validators=hooks.get('validate',[])
        if isinstance(validators,str): validators=[validators]
        if any('invoice_attachment' in str(v) for v in validators):
            raise RuntimeError('Old attachment validation is still active; cleanup is required first.')
        get_jenv().from_string(template)
        from self_test import run_self_tests
        print('Template regression checks passed: '+str(run_self_tests(template)))
        before=fingerprint()
        format_doc=frappe.get_doc('Print Format',FORMAT)
        original=format_doc.as_dict()
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        run_dir=Path(frappe.get_site_path('private','backups','dynamic_invoice_print_'+stamp))
        run_dir.mkdir(parents=True,exist_ok=False)
        (run_dir/'print_format.before.json').write_text(json.dumps(original,default=str,ensure_ascii=False,indent=2),encoding='utf8')
        format_doc.format_data=prepare(format_doc,template)
        format_doc.save()
        frappe.clear_cache(doctype='Print Format')
        from frappe.utils.pdf import get_pdf
        preview=package/'previews'/stamp
        preview.mkdir(parents=True,exist_ok=False)
        summaries={}
        for name in SAMPLES:
            invoice=frappe.get_doc('Sales Invoice',name)
            summaries[name]=source_summary(invoice)
            html=frappe.get_print('Sales Invoice',name,print_format=FORMAT,doc=invoice)
            if 'blitz-source-items' not in html:
                raise RuntimeError('New items block did not render for '+name)
            rendered_groups=check_rendered_groups(html,summaries[name])
            (preview/(name+'.html')).write_text(html,encoding='utf8')
            preview_html,missing_images=local_preview_images(html)
            (preview/(name+'.preview.html')).write_text(preview_html,encoding='utf8')
            pdf=get_pdf(preview_html)
            if not pdf.startswith(b'%PDF-'):
                raise RuntimeError('PDF rendering failed for '+name)
            (preview/(name+'.pdf')).write_bytes(pdf)
            print(name+': HTML and PDF generated; item/source counts '+json.dumps(summaries[name]))
            print('Printed groups: '+json.dumps(rendered_groups))
            if missing_images:
                print('Preview only: '+str(missing_images)+' unavailable image(s) replaced with a transparent placeholder. Letter Head unchanged.')
        after=fingerprint()
        if before!=after:
            raise RuntimeError('Protected transaction data changed. Rolling back.')
        verification={'transaction_data_unchanged':True,'samples':summaries,'applied':args.apply,
                      'preview_directory':str(preview),'backup_directory':str(run_dir)}
        (run_dir/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf8')
        if args.apply:
            frappe.db.commit()
            print('APPLIED: only the items block of PPN TEST was replaced.')
        else:
            frappe.db.rollback()
            print('PREVIEW ONLY: database change rolled back. Use --apply to keep the new print table.')
        print('Local preview folder: '+str(preview))
        print('Backup folder: '+str(run_dir))
    except Exception:
        frappe.db.rollback()
        print('STOPPED: database changes rolled back. Existing previews, if any, are private local files.')
        raise
    finally:
        frappe.clear_cache(doctype='Print Format')
        frappe.destroy()


if __name__=='__main__':
    main()
