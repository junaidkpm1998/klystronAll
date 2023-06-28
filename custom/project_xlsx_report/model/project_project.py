from base64 import encodebytes
from datetime import datetime
from io import BytesIO

from xlsxwriter import workbook

from odoo import models, fields

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProjectXlsxReport(models.Model):
    _inherit = "project.project"

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        print("HHH")
        print(self.analytic_account_id.partner_id,"purchase_orders_count")
        sheet = workbook.add_worksheet('PROJECT XLSX REPORT')
        format0 = workbook.add_format({'font_size': 14, 'align': 'center'})
        format1 = workbook.add_format({'font_size': 10, 'align': 'vcenter'})
        format2 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 11, 'align': 'center', })
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})
        border_text_centr = workbook.add_format(
            {'border': 1, 'align': 'center', 'font_size': 14})
        row = 6
        col = 0
        # sheet.merge_range(row, 2, row, 10, 'PROJECT XLSX REPORT', border_text_centr)

        sheet.write(4, 1, 'Project Name', format11)
        sheet.write(4, 2, self.name, format11)

        sheet.write(5, 1, self.partner_id.name, border_text_centr)
        # sheet.set_column(0, 0, 20)
        sheet.set_column(1, 5, 20)




        # sheet.merge_range(row + 2, 1, row + 3, 2, 'PO', border_text_centr)
        # sheet.merge_range(row + 2, 3, row + 3, 4, 'AMOUNT', border_text_centr)
        # sheet.merge_range(row + 2, 5, row + 3, 7, 'BALANCE AMOUNT', border_text_centr)
        # sheet.merge_range(row + 2, 8, row + 3, 10, 'TOTAL AMOUNT', border_text_centr)
        # sheet.merge_range(row + 2, 11, row + 3, 13, 'PAYMENT STATUS', border_text_centr)

        sheet.write(8, 1, 'PO', border_text_centr)
        sheet.write(8, 2, 'AMOUNT', border_text_centr)
        sheet.write(8, 3, 'BALANCE AMOUNT', border_text_centr)
        sheet.write(8, 4, 'TOTAL AMOUNT', border_text_centr)
        sheet.write(8, 5, 'PAYMENT STATUS', border_text_centr)











        # sheet.merge_range(row, 1, row, 7, 'PROJECT XLSX REPORT', border_text_centr)

    def xlsx_print(self):
        print('sjkdhnf')
        active_ids_tmp = self.env.context.get('active_ids')
        # print('active_ids_tmp', active_ids_tmp)
        active_model = self.env.context.get('active_model')
        # print('active_model', active_model)
        data = {
            # 'output_type': self.read()[0]['output_type'][0],
            'ids': active_ids_tmp,
            'project_name': self.name,
            'vendor': self.partner_id.name,
            'context': {'active_model': active_model},
        }
        # print('data', data)
        file_io = BytesIO()
        # print('kds', file_io)
        workbook = xlsxwriter.Workbook(file_io)
        # print('sd', workbook)
        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())
        # print('sdkf', fout)
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        # print('date', datetime_string)
        report_name = 'PROJECT XLSX REPORT'
        # print('dsf', report_name)
        filename = '%s_%s' % (report_name, datetime_string)
        # print('file', filename)
        # print(self)

        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'
        # print(filename)

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }
