import xlsxwriter
import time
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from io import BytesIO

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes

from odoo.tools import float_is_zero
from odoo.tools import date_utils
import io
import json


class TravelManagementWizard(models.TransientModel):
    _name = 'travel.management.wizard'

    starting_date = fields.Date(string="Date")
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def tm_query(self):
        query = """select travel_management.name as sequence,res_partner.name as customer,
        tm_service_types.name as service,travel_management.date as date,rs.name ->> 'en_US' as source_location,
        rc.name ->> 'en_US' as destination_location
        from travel_management
        inner join res_partner
        on travel_management.customer_id = res_partner.id
        inner join tm_service_types
        on travel_management.service_id = tm_service_types.id
        inner join res_country as rs
        on travel_management.source_location_id = rs.id 
        inner join res_country as rc
        on travel_management.dest_location_id = rc.id"""
        cr = self._cr
        cr.execute(query)
        sql_dict = self._cr.dictfetchall()
        return sql_dict


    def action_tm_pdf_report(self):
        print("fii")
        data = {
            'sql_data': self.tm_query()

        }
        return self.env.ref('travel_management.action_pdf_report_travel_management').report_action(None, data=data)

    def action_tm_xls_report(self):
        print("hhhhhhhhhh")
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {
            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Inventory Ageing Report'
        filename = '%s_%s' % (report_name, datetime_string)
        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        date_style = workbook.add_format({'align': 'center','font_size': '10px','num_format': 'dd-mm-yyyy'})
        sheet = workbook.add_worksheet("Travel Management Report")
        sheet.set_column(1, 6, 18)

        align = workbook.add_format({'font_size': '10px', 'align': 'center', 'border': 1})
        cell_format = workbook.add_format({'font_size': '12px', 'bold': True})
        heading = workbook.add_format({'font_size': '10px', 'align': 'center', 'border': 1, 'bold': True})
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px', 'font_color': 'red'})
        txt = workbook.add_format({'align': 'center', 'font_size': '10px'})
        sheet.merge_range('B2:G3', 'Travel Management Report', head)
        sheet.write(6,1, 'Sequence NO:', heading)
        sheet.write(6,2, 'Customer', heading)
        sheet.write(6,3, 'Service', heading)
        sheet.write(6,4, 'Source', heading)
        sheet.write(6,5, 'Source Location', heading)
        sheet.write(6,6, 'Dest: Location', heading)
        
        row = 7
        for line in self.tm_query():
            sheet.set_row(row, 20)
            sheet.write(row, 1, line['sequence'], txt)
            sheet.write(row, 2, line['customer'], txt)
            sheet.write(row, 3, line['service'], txt)
            sheet.write(row, 4, line['date'], date_style)
            sheet.write(row, 5, line['source_location'], txt)
            sheet.write(row, 6, line['destination_location'], txt)
            row += 1
        workbook.close()


