import io

import xlsxwriter

from odoo import http
from odoo.http import request, content_disposition


class InvoiceExcelReportController(http.Controller):
    @http.route([
        '/invoicing/excel_report/<model("warranty.wizard.model"):report_id>',
    ], type='http', auth="user", csrf=False)
    def get_sale_excel_report(self, report_id=None, text_style=None, **args):

        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Warranty Report' + '.xlsx'))
            ]
        )
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_style = workbook.add_format({'align': 'center', 'font_size': '15px', 'bold': True})
        main_header_style =  workbook.add_format({'align': 'center','font_size': '12px','bold': True,'border': 2})
        text_style = workbook.add_format({'align': 'center'})
        # get data for the report.
        report_lines = report_id.get_report_lines()
        sql_data = report_lines.get('sql_data')
        company = report_lines.get('company')

        sheet = workbook.add_worksheet("warranty")
        sheet.set_column(1,4,30)
        sheet.merge_range('B3:E3', "PRODUCT WARRANTY", main_header_style)
        # sheet.write(1, 1,  header_style)
        # sheet.write(1, 1, company['company'], text_style)

        # print(request.env.company.name)



        # sheet.set_rows(6,7,5)
        sheet.write(5, 1, 'ID', header_style)
        sheet.write(5, 2, 'Invoice ', header_style)
        sheet.write(5, 3, 'Customer', header_style)
        sheet.write(5, 4, 'Product', header_style)

        row = 7
        for line in sql_data:
            sheet.set_row(row, 20)
            sheet.write(row, 1, line['id'], text_style)
            sheet.write(row, 2, line['invoice'], text_style)
            sheet.write(row, 3, line['customer'], text_style)
            sheet.write(row, 4, line['product'], text_style)

            row += 1
            # number += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
        return response
