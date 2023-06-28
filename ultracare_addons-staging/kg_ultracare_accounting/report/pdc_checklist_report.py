import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class PDCChecklistReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.pdc_checklist_template'
    _description = 'PDC Checklist Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        sum_amount = 0
        pdc_id = self.env['pdc.wizard'].search(
            [('payment_date', '>=', date_from), ('payment_date', '<=', date_end),
             ('state', '!=', ['draft', 'returned', 'cancel'])])
        for vals in pdc_id:
            trno = vals.memo
            date = vals.invoice_id.invoice_date
            cheque_date = vals.payment_date
            cheque_no = vals.name
            description = vals.reference
            amount = vals.payment_amount

            pdc_vals = {
                'type': 'data',
                'trno': trno,
                'date': date,
                'cheque_date': cheque_date,
                'cheque_no': cheque_no,
                'description': description,
                'amount': amount,
            }
            data.append(pdc_vals)

            sum_amount += amount
        pdc_vals = {
            'type':'amount',
            'sum_amount':sum_amount
        }
        if sum_amount != 0:
            data.append(pdc_vals)
        sum_amount = 0

        return {
            'doc_ids': self.ids,
            'datas': data,
            'from_date': date_from,
            'to_date': date_end,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
        }
