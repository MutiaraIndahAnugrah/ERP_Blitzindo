"""Template regression tests, using Frappe's actual Jinja sandbox in WSL."""
from html.parser import HTMLParser
from types import SimpleNamespace


class Doc(SimpleNamespace):
    def get(self, key, default=None):
        return getattr(self,key,default)

    def has_permission(self, permission):
        return getattr(self,'allowed',True)


class Counter(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=0; self.heads=0; self.cells=[]; self.current=None; self.groups=[]

    def handle_starttag(self,tag,attrs):
        if tag=='table': self.tables+=1; self.groups.append(dict(attrs))
        if tag=='thead': self.heads+=1
        if tag=='td': self.current=''

    def handle_data(self,data):
        if self.current is not None: self.current+=data

    def handle_endtag(self,tag):
        if tag=='td':
            self.cells.append((self.current or '').strip());self.current=None


def run_self_tests(template):
    from frappe.utils.jinja import get_jenv
    compiled=get_jenv().from_string(template)
    documents={}
    def item(idx,qty,order):
        return Doc(idx=idx,qty=qty,rate=100,amount=qty*100,detail_order=order,
                   item_name='SERVICE-'+str(idx),item_code='ITEM-'+str(idx),uom='Process')
    def detail(idx):
        return Doc(data_tka=None,nama_tka='Sample '+str(idx),foreign_name='',
                   no_passport_tka='MASKED-'+str(idx),jangka_waktu='12 Bulan')
    def source(name,count):
        documents[('Detail Order',name)]=Doc(name=name,docstatus=0,details=[detail(i) for i in range(count)],wo_number=None)
    def get_doc(dt,name): return documents[(dt,name)]
    def exists(dt,name): return (dt,name) in documents
    so_links={}
    def get_value(dt,name,*args,**kwargs):
        if dt=='Sales Order Item': return so_links.get(name)
        return name if (dt,name) in documents else None
    result_rows=[]
    def get_all(dt,filters,fields):
        assert dt=='Result Document'
        assert set(filters)=={'tka','work_orders','docstatus'}
        return [Doc(name=r.name) for r in result_rows
                if r.tka==filters['tka'] and r.work_orders==filters['work_orders']]
    fake=Doc(get_doc=get_doc,get_all=get_all,db=Doc(exists=exists,get_value=get_value),
             format_value=lambda value,opts: ('%.*f' % (int(opts.get('precision',2)),float(value or 0))))
    def render(items):
        documents[('Sales Invoice','TEST')]=Doc(name='TEST',items=items,currency='IDR')
        # The print object is deliberately grouped and must not be the data source.
        html=compiled.render(doc=Doc(name='TEST',items=[item(1,999,None)]),frappe=fake)
        c=Counter();c.feed(html)
        return html,c
    checks=0
    source('DO-A',32);source('DO-B',1);source('DO-C',2)
    html,c=render([item(1,13,'DO-A'),item(2,1,'DO-B'),item(3,2,'DO-C')])
    assert c.tables==3 and c.heads==3;checks+=1
    assert sum(cell.startswith('Sample ') for cell in c.cells)==35;checks+=1
    assert '999.00' not in html;checks+=1
    assert 'Jumlah rincian sumber berbeda' not in html;checks+=1
    assert c.cells.count('100.00')==35;checks+=1
    assert 'Harga / Process (IDR)' in html and 'Total tagihan:' in html;checks+=1
    assert c.groups[0]['data-blitz-billed-amount']=='1300' and c.groups[0]['data-blitz-detail-count']=='32';checks+=1
    html,c=render([item(1,10,None)])
    assert 'Rincian belum tertaut' in html;checks+=1
    source('DO-A',1)
    recovered=item(1,1,None);recovered.so_detail='SO-ROW';recovered.sales_order='SO-A'
    so_links['SO-ROW']=Doc(parent='SO-A',detail_order='DO-A')
    html,c=render([recovered]);assert any(cell.startswith('Sample ') for cell in c.cells);checks+=1
    so_links['SO-ROW'].parent='OTHER-SO'
    html,c=render([recovered]);assert 'Rincian belum tertaut' in html;checks+=1
    documents[('Detail Order','DO-A')].allowed=False
    html,c=render([item(1,1,'DO-A')]);assert not any(cell.startswith('Sample ') for cell in c.cells);checks+=1
    documents[('Detail Order','DO-A')].allowed=True
    d=documents[('Detail Order','DO-A')].details[0]
    d.nama_tka='<script>alert(1)</script>'
    html,c=render([item(1,1,'DO-A')]);assert '<script>' not in html and '&lt;script&gt;' in html;checks+=1
    d.nama_tka=None;d.no_passport_tka=None;d.data_tka='WORKER'
    documents[('Tenaga Kerja','WORKER')]=Doc(full_name='Live Sample',no_passport='MASKED',nama_asing='')
    html,c=render([item(1,1,'DO-A')]);assert 'Live Sample' in c.cells;checks+=1
    documents[('Detail Order','DO-A')].wo_number='WO-A'
    result_rows.extend([Doc(name='RD-A',tka='WORKER',work_orders='WO-A'),Doc(name='RD-B',tka='WORKER',work_orders='WO-B')])
    documents[('Result Document','RD-A')]=Doc(visa='Visa source A')
    documents[('Result Document','RD-B')]=Doc(visa='WRONG VISA')
    html,c=render([item(1,1,'DO-A')]);assert 'Visa source A' in c.cells and 'WRONG VISA' not in html;checks+=1
    documents[('Result Document','RD-A')].allowed=False
    html,c=render([item(1,1,'DO-A')]);assert 'Visa source A' not in html;checks+=1
    fractional=item(1,0.5,None)
    html,c=render([fractional]);assert '0.50' in html;checks+=1
    # Same service / duration / price across different DOs becomes one group.
    source('DO-A',32);source('DO-B',1);source('DO-C',2)
    a=item(1,13,'DO-A'); b=item(2,1,'DO-B'); citem=item(3,2,'DO-C')
    b.item_code=citem.item_code='DPKK-12'; b.item_name=citem.item_name='DPKK'
    html,c=render([a,b,citem])
    assert c.tables==2 and c.groups[1]['data-blitz-item-rows']=='2,3'; checks+=1
    assert c.groups[1]['data-blitz-detail-count']=='3' and float(c.groups[1]['data-blitz-billed-qty'])==3;checks+=1
    assert 'Visa terkait sumber' not in html;checks+=1
    # Every optional column is hidden if the whole group has no values.
    empty=documents[('Detail Order','DO-B')].details[0]
    empty.no_passport_tka=None;empty.jangka_waktu=None
    html,c=render([b])
    assert 'No. paspor' not in html and '<th>Durasi</th>' not in html;checks+=1
    # Restored duration differs: do not merge even though item code and rate match.
    empty.jangka_waktu='6 Bulan';empty.no_passport_tka='MASKED'
    html,c=render([b,citem]);assert c.tables==2;checks+=1
    empty.jangka_waktu='12 Bulan'
    citem.rate=101;citem.amount=202
    html,c=render([b,citem]);assert c.tables==2;checks+=1
    citem.rate=100;citem.amount=200;citem.uom='Months'
    html,c=render([b,citem]);assert c.tables==2;checks+=1
    # A real visa keeps its column, unlike empty DPKK groups.
    documents[('Detail Order','DO-B')].wo_number='WO-A'
    empty.data_tka='WORKER';documents[('Result Document','RD-A')].allowed=True
    html,c=render([b]);assert 'Visa terkait sumber' in html and 'Visa source A' in html;checks+=1
    return checks
