import time
from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class CustomerAnalysisReport(models.AbstractModel):
    _name = 'report.kg_ultracare_sale.customer_analysis_report_template'
    _description = 'Customer Analysis Report'

    def search_sub_total(self, date_from, date_end, prd):
        account_line_id = self.env['account.move.line'].search(
            [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
             ('move_id.state', '=', 'posted'), ('product_id', '=', prd.id)])
        return sum(account_line_id.mapped('quantity'))


    @api.model
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

        partner_id = self.env['res.partner'].search([])
        data_list = []
        jan = 0
        feb = 0
        mar = 0
        apr = 0
        may = 0
        jun = 0
        jul = 0
        aug = 0
        sep = 0
        oct = 0
        nov = 0
        dec = 0
        quanity_total = 0
        for customer in partner_id:
            account_line = self.env['account.move.line'].search(
                [('move_id.invoice_date', '>=', date_from), ('move_id.invoice_date', '<=', date_end),
                 ('move_id.state', '=', 'posted'), ('move_id.partner_id', '=', customer.id)], order='product_id asc')

            customer_name = str(customer.name).upper()
            customer_code = str(customer.customer_code).upper()
            account_move_line = {'type': 'customer',
                                 'customer_name': customer_name,
                                 'customer_code': customer_code,
                                 }
            if len(account_line) > 0:
                data_list.append(account_move_line)

            if len(account_line) > 0:
                product = account_line[0].product_id.id
                inr = 0
                subtotal = 0
                quantity = 0
                while (inr < len(account_line)):
                    if account_line[inr].product_id.id == product:
                        subtotal += account_line[inr].price_subtotal
                        quantity += account_line[inr].quantity
                    else:
                        rtn_line = self.env['account.move.line'].search(
                            [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
                             ('move_id.state', '=', 'posted'),
                             ('product_id', '=', product)])
                        prd = rtn_line.product_id
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

                        jan_qty = self.search_sub_total(jan_start, jan_end, prd)
                        feb_qty = self.search_sub_total(feb_start, feb_end, prd)
                        mar_qty = self.search_sub_total(mar_start, mar_end, prd)
                        apr_qty = self.search_sub_total(apr_start, apr_end, prd)
                        may_qty = self.search_sub_total(may_start, may_end, prd)
                        jun_qty = self.search_sub_total(jun_start, jun_end, prd)
                        jul_qty = self.search_sub_total(jul_start, jul_end, prd)
                        aug_qty = self.search_sub_total(aug_start, aug_end, prd)
                        sep_qty = self.search_sub_total(sep_start, sep_end, prd)
                        oct_qty = self.search_sub_total(oct_start, oct_end, prd)
                        nov_qty = self.search_sub_total(nov_start, nov_end, prd)
                        dec_qty = self.search_sub_total(dec_start, dec_end, prd)

                        total = jan_qty + feb_qty + mar_qty + apr_qty + may_qty + jun_qty + jul_qty + aug_qty + sep_qty + oct_qty + nov_qty + dec_qty

                        data_list.append(
                            {
                                'type': 'data',
                                'item_code': str(account_line[inr - 1].product_id.default_code).upper(),
                                'subtotal': subtotal,
                                'quantity': quantity,
                                'total': total,
                                'jan_qty': jan_qty,
                                'feb_qty': feb_qty,
                                'mar_qty': mar_qty,
                                'apr_qty': apr_qty,
                                'may_qty': may_qty,
                                'jun_qty': jun_qty,
                                'jul_qty': jul_qty,
                                'aug_qty': aug_qty,
                                'sep_qty': sep_qty,
                                'oct_qty': oct_qty,
                                'nov_qty': nov_qty,
                                'dec_qty': dec_qty,
                            })

                        jan += jan_qty
                        feb += feb_qty
                        mar += mar_qty
                        apr += apr_qty
                        may += may_qty
                        jun += jun_qty
                        jul += jul_qty
                        aug += aug_qty
                        sep += sep_qty
                        oct += oct_qty
                        nov += nov_qty
                        dec += dec_qty
                        quanity_total += total

                        product = account_line[inr].product_id.id
                        subtotal = 0
                        quantity = 0
                        subtotal += account_line[inr].price_subtotal
                        quantity += account_line[inr].quantity
                    inr += 1

                rtn_line = self.env['account.move.line'].search(
                    [('move_id.invoice_date', '<=', date_end), ('move_id.invoice_date', '>=', date_from),
                     ('move_id.state', '=', 'posted'), ('product_id', '=', account_line[inr - 1].product_id.id),
                     ])
                prd = rtn_line.product_id
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

                jan_qty = self.search_sub_total(jan_start, jan_end, prd)
                feb_qty = self.search_sub_total(feb_start, feb_end, prd)
                mar_qty = self.search_sub_total(mar_start, mar_end, prd)
                apr_qty = self.search_sub_total(apr_start, apr_end, prd)
                may_qty = self.search_sub_total(may_start, may_end, prd)
                jun_qty = self.search_sub_total(jun_start, jun_end, prd)
                jul_qty = self.search_sub_total(jul_start, jul_end, prd)
                aug_qty = self.search_sub_total(aug_start, aug_end, prd)
                sep_qty = self.search_sub_total(sep_start, sep_end, prd)
                oct_qty = self.search_sub_total(oct_start, oct_end, prd)
                nov_qty = self.search_sub_total(nov_start, nov_end, prd)
                dec_qty = self.search_sub_total(dec_start, dec_end, prd)

                total = jan_qty + feb_qty + mar_qty + apr_qty + may_qty + jun_qty + jul_qty + aug_qty + sep_qty + oct_qty + nov_qty + dec_qty

                data_list.append(
                    {
                        'type': 'data',
                        'item_code': str(account_line[inr - 1].product_id.default_code).upper(),
                        'product_name': str(account_line[inr - 1].product_id.name).upper(),
                        'subtotal': subtotal,
                        'quantity': quantity,
                        'total': total,
                        'jan_qty': jan_qty,
                        'feb_qty': feb_qty,
                        'mar_qty': mar_qty,
                        'apr_qty': apr_qty,
                        'may_qty': may_qty,
                        'jun_qty': jun_qty,
                        'jul_qty': jul_qty,
                        'aug_qty': aug_qty,
                        'sep_qty': sep_qty,
                        'oct_qty': oct_qty,
                        'nov_qty': nov_qty,
                        'dec_qty': dec_qty,
                    })
                jan += jan_qty
                feb += feb_qty
                mar += mar_qty
                apr += apr_qty
                may += may_qty
                jun += jun_qty
                jul += jul_qty
                aug += aug_qty
                sep += sep_qty
                oct += oct_qty
                nov += nov_qty
                dec += dec_qty
                quanity_total += total

                account_move_line = {'type': 'amount',
                                     'total_jan': jan,
                                     'total_feb': feb,
                                     'total_mar': mar,
                                     'total_apr': apr,
                                     'total_may': may,
                                     'total_jun': jun,
                                     'total_jul': jul,
                                     'total_aug': aug,
                                     'total_sep': sep,
                                     'total_oct': oct,
                                     'total_nov': nov,
                                     'total_dec': dec,
                                     'total_qty': quanity_total,
                                     }
                data_list.append(account_move_line)
                jan = 0
                feb = 0
                mar = 0
                apr = 0
                may = 0
                jun = 0
                jul = 0
                aug = 0
                sep = 0
                oct = 0
                nov = 0
                dec = 0
                quanity_total = 0

        # if not data_list:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data_list,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'from_date': date_from,
            'to_date': date_end
        }
