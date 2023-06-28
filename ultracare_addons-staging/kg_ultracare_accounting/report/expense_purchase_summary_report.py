import time
from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class ExpensePurchaseSummaryReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.expense_pur_sum_tem_id'
    _description = 'Expense Purchase Summary Report'

    def search_total(self, date_from, date_end):
        account_line_id = self.env['account.move'].search(
            [('invoice_date', '>=', date_from), ('invoice_date', '<=', date_end), ('state', '=', 'posted'),
             ('move_type', '=', 'in_invoice')])
        return sum(account_line_id.mapped('amount_total_in_currency_signed'))

    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        year = data['form'].get('year')

        date_start = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_from = datetime.strptime(date_start, '%Y-%m-%d')

        end_date = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        date_end = datetime.strptime(end_date, '%Y-%m-%d')

        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []

        jan_start = '01-01-' + str(year)
        jan_end = '31-01-' + str(year)

        feb_start = '01-02-' + str(year)
        feb_end = '28-02-' + str(year)

        mar_start = '01-03-' + str(year)
        mar_end = '31-03-' + str(year)

        apr_start = '01-04-' + str(year)
        apr_end = '30-04-' + str(year)

        may_start = '01-05-' + str(year)
        may_end = '31-05-' + str(year)

        jun_start = '01-06-' + str(year)
        jun_end = '30-06-' + str(year)

        jul_start = '01-07-' + str(year)
        jul_end = '31-07-' + str(year)

        aug_start = '01-08-' + str(year)
        aug_end = '31-08-' + str(year)

        sep_start = '01-09-' + str(year)
        sep_end = '30-09-' + str(year)

        oct_start = '01-10-' + str(year)
        oct_end = '31-10-' + str(year)

        nov_start = '01-11-' + str(year)
        nov_end = '30-11-' + str(year)

        dec_start = '01-12-' + str(year)
        dec_end = '31-12-' + str(year)

        jan_amount = self.search_total(jan_start, jan_end)
        feb_amount = self.search_total(feb_start, feb_end)
        mar_amount = self.search_total(mar_start, mar_end)
        apr_amount = self.search_total(apr_start, apr_end)
        may_amount = self.search_total(may_start, may_end)
        jun_amount = self.search_total(jun_start, jun_end)
        jul_amount = self.search_total(jul_start, jul_end)
        aug_amount = self.search_total(aug_start, aug_end)
        sep_amount = self.search_total(sep_start, sep_end)
        oct_amount = self.search_total(oct_start, oct_end)
        nov_amount = self.search_total(nov_start, nov_end)
        dec_amount = self.search_total(dec_start, dec_end)

        total_amount = jan_amount + feb_amount + mar_amount + apr_amount + may_amount + jun_amount + jul_amount + aug_amount + sep_amount + oct_amount + nov_amount + dec_amount

        vendor_bill_list = {
            'type': 'data',
            'jan_amount': jan_amount,
            'feb_amount': feb_amount,
            'mar_amount': mar_amount,
            'apr_amount': apr_amount,
            'may_amount': may_amount,
            'jun_amount': jun_amount,
            'jul_amount': jul_amount,
            'aug_amount': aug_amount,
            'sep_amount': sep_amount,
            'oct_amount': oct_amount,
            'nov_amount': nov_amount,
            'dec_amount': dec_amount,
            'total_amount': total_amount,
        }
        data.append(vendor_bill_list)

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }
