import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import image_data_uri


class PurchaseAccountDetailsReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.purchase_bill_register_template'
    _description = 'Pending Purchase Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        report_type = data['form'].get('report_type')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])
        data = []
        partner_id = self.env['res.partner'].search([])
        move = self.env['account.move'].search(
            [('invoice_date', '>=', date_from), ('invoice_date', '<=', date_end),
             ('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        print(move,"Moveee")
        values = []
        for i in move.line_ids:
            vals = i.filtered(lambda x: x.debit > 0)
            if vals:
                lines = {
                    'date': vals.move_id.invoice_date,
                    'doc_no': vals.move_id.name,
                    'ref': vals.move_id.ref,
                    'account_code': vals.account_id.code,
                    'account_name': vals.account_id.name,
                    'debit': vals.debit,
                    'customer_code': vals.move_id.partner_id.customer_code,
                    'customer_name': vals.move_id.partner_id.name,
                    'account_description': vals.move_id.name
                }
                values.append(lines)

        return {
            'values': values,
            'from_date': date_from,
            'to_date': date_end,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'logo': browsed_company.logo and image_data_uri(browsed_company.logo),
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name
        }
