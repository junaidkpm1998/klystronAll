import io

import xlsxwriter

from odoo import models, fields
from odoo.addons.test_convert.tests.test_env import data
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from odoo.tools.safe_eval import json


class WizardModel(models.Model):
    _name = "warranty.wizard.model"

    wizard_product_id = fields.Many2one('product.product')
    wizard_customer_id = fields.Many2one('res.partner')
    warranty_start_date = fields.Date(string="Warranty Start Date")
    warranty_end_date = fields.Date(string="Warranty End Date")

    def action_query(self):
        query = """SELECT warranty_model.name as id,account_move.name as invoice,res_partner.name as customer,product_template.name->> 'en_US'  As product
        FROM warranty_model
        inner join account_move
        on warranty_model.invoice_id = account_move.id
        inner join res_partner
        on account_move.partner_id = res_partner.id
        inner join product_product
        on warranty_model.product_id = product_product.id
        inner join product_template
        on product_product.product_tmpl_id = product_template.id
        """

        if self.wizard_product_id:
            query += """AND product_product.id = '%s'""" % self.wizard_product_id.id
        if self.wizard_customer_id:
            query += """AND account_move.partner_id = '%s'""" % self.wizard_customer_id.id
        if self.warranty_start_date:
            query += """AND warranty_model.request_date >= '%s'""" % self.warranty_start_date
        if self.warranty_end_date:
            if self.warranty_start_date > self.warranty_end_date:
                raise ValidationError(("End date is grater than start date"))
            else:
                query += """AND warranty_model.request_date <= '%s'""" % self.warranty_end_date

        cr = self._cr
        cr.execute(query)
        sql_dict = self._cr.dictfetchall()
        return sql_dict

    def action_pdf_report(self):
        data = {

            'sql_data': self.action_query()

        }
        return self.env.ref('product_warranty.action_pdf_report_product_warranty').report_action(None, data=data)

    def action_xls_report(self):
        print("xls")
        return {
            'type': 'ir.actions.act_url',
            'url': '/invoicing/excel_report/%s' % (self.id),
            'target': 'new',
        }

    def get_report_lines(self):
        data = {
            'sql_data': self.action_query()
        }
        return data

    def print_xlsx(self):
        if self.warranty_start_date > self.warranty_end_date:
            raise ValidationError('Start Date must be less than End Date')
        data = {
            'warranty_start_date': self.warranty_start_date,
            'warranty_end_date': self.warranty_end_date,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'warranty.wizard.model',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        sheet.set_column(1, 4, 30)

        main_header_style = workbook.add_format({'align': 'center', 'font_size': '12px', 'bold': True, 'border': 2})

        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '15px'})
        sheet.merge_range('B3:E3', "PRODUCT WARRANTY", main_header_style)
        sheet.write(5, 1, 'ID', head)
        sheet.write(5, 2, 'Invoice ', head)
        sheet.write(5, 3, 'Customer', head)
        sheet.write(5, 4, 'Product', head)

        row = 7
        for line in self.action_query():
            sheet.set_row(row, 20)
            sheet.write(row, 1, line['id'], cell_format)
            sheet.write(row, 2, line['invoice'], cell_format)
            sheet.write(row, 3, line['customer'], cell_format)
            sheet.write(row, 4, line['product'], cell_format)

            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
