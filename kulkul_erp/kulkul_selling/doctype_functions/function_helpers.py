import frappe
import datetime

def update_current_value_series(doc):
    posting_date = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    month_and_year = "{:02d}{}".format(posting_date.month, str(posting_date.year)[2:4])

    naming_series = ""
    if doc.doctype == 'Payment Entry':
        naming_series = "{}-{}-{}-".format(doc.naming_series[:-16], month_and_year, doc.naming_series[-7:][:1])
    elif doc.doctype == 'Journal Entry':
        if len(doc.naming_series) == 16:
            naming_series = "{}-{}-".format(doc.naming_series[:2], month_and_year)
        elif len(doc.naming_series) == 20:
            naming_series = "{}-{}-{}-".format(doc.naming_series[:2], doc.naming_series[4:6], month_and_year)
        elif len(doc.naming_series) == 22:
            naming_series = "{}-{}-{}-{}-".format(doc.naming_series[:2], doc.naming_series[4:6], month_and_year, doc.naming_series[-7:][:1])
        elif len(doc.naming_series) == 24:
            naming_series = "{}-{}-{}-{}-".format(doc.naming_series[:2], doc.naming_series[4:8], month_and_year, doc.naming_series[-7:][:1])
    else:
        naming_series = "{}-{}-".format(doc.naming_series[:-14], month_and_year)
        
    series = frappe.db.sql("""
        SELECT * FROM `tabSeries` WHERE name = "{}" LIMIT 1
    """.format(naming_series), as_dict=1)

    if series and len(series) > 0:
        all_series = frappe.db.sql("""
            SELECT CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) AS name 
            FROM `tab{}` 
            WHERE amended_from IS NULL AND name LIKE 
            "{}%" ORDER BY CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) ASC
        """.format(doc.doctype, naming_series[:-1]), as_dict=1)

        missing_number_one = False

        if len(all_series) > 0:
            array_series = pluck(all_series, 'name')

            if int(array_series[0]) != 1:
                array_series.insert(0, 1)
                missing_number_one = True

            missing_series = find_missing(array_series)

            if len(missing_series) > 0:
                new_last_value = int(missing_series[0]) - 1
            else:
                last_number = frappe.db.sql("""
                    SELECT CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) AS name 
                    FROM `tab{}` 
                    WHERE amended_from IS NULL AND name LIKE 
                    "{}%" ORDER BY CAST(SUBSTRING_INDEX(name,'-', -1) AS SIGNED) DESC LIMIT 1
                """.format(doc.doctype, naming_series[:-1]), as_dict=1)

                if len(last_number) > 0:
                    new_last_value = int(last_number[0].name)
                else:
                    new_last_value = 0
            
            if missing_number_one == True:
                new_last_value = 0
        else:
            new_last_value = 0
            missing_series = []
            array_series = []

        frappe.db.sql("""
            UPDATE `tabSeries` SET current = "{}" WHERE name = "{}"
        """.format(new_last_value, series[0].name))
        
        access_log = frappe.get_last_doc('Access Log')

        frappe.db.sql("""
            UPDATE `tabSeries` SET current = "{}" WHERE name = " "
        """.format(int(access_log.name[3:])))

        frappe.db.commit()

def pluck(lst, key):
    return [x.get(key) for x in lst]

def find_missing(lst):
    return [x for x in range(lst[0], lst[-1]+1)
            if x not in lst]