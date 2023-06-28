# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
from datetime import datetime

from odoo import api, models, _
from dateutil.relativedelta import relativedelta
import time
from odoo.exceptions import UserError, ValidationError

from odoo.exceptions import ValidationError
from odoo.tools import float_repr, float_is_zero


# from odoo.exceptions import Warning


class COnsolidated_ageing_receivabled_report(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.consolidated_ageing_rec_template'
    _description = 'Consolidated Ageing Receivables Report '

    def _get_partner_move_lines(self, account_type, date_from, period_length, period_length_months,
                                period_length_type, uneven, period_leght_uneven, data):
        # This method can receive
        # the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        periods = {}
        start = datetime.strptime(str(date_from), "%Y-%m-%d")
        date_from = datetime.strptime(str(date_from), "%Y-%m-%d").date()
        range_count = 6
        if uneven:
            range_count = period_leght_uneven + 1

        if period_length_type == 'months':
            range_count = period_length_months
            count = period_length_months
            for i in range(period_length_months)[period_length_months::-1]:
                stop = start - relativedelta(months=1)
                if i == 0:
                    period_name = '>=' + str(stop.strftime("%b")) + '-' + str(stop.year)
                else:
                    period_name = str(stop.strftime("%b")) + '-' + str(stop.year)
                period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
                periods[str(i)] = {
                    'name': period_name,
                    'stop': period_stop,
                    'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
                }
                start = stop
                count = count - 1
        if period_length_type == 'days':
            if uneven:
                periods = data['periods']
            else:
                for i in range(range_count)[::-1]:
                    stop = start - relativedelta(days=period_length)
                    period_name = str((6 - (i + 1)) * period_length + 1) + '-' + str((6 - i) * period_length)
                    period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
                    a = 0
                    if i == 0:
                        a += 1
                        period_name = '+' + str(5 * period_length)
                    periods[str(i)] = {
                        'name': period_name,
                        'stop': period_stop,
                        'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
                    }
                    start = stop

        res = []
        total = []
        pdc_ttl = []
        cr = self.env.cr
        user_company = self.env.user.company_id
        user_currency = user_company.currency_id
        ResCurrency = self.env['res.currency'].with_context(date=date_from)
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        arg_list = (tuple(move_state), tuple(account_type))
        # build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where max_date > %s',
                   (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name), l.account_id
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
            AND (l.move_id = am.id)
            AND (am.state IN %s)
            AND (account_account.account_type IN %s)
            AND ''' + reconciliation_clause + '''
            AND (l.date <= %s)
            AND l.company_id IN %s
        ORDER BY UPPER(res_partner.name),l.account_id'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(range_count + 2):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        paid_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) 
                AND (l.move_id = am.id)
            AND (am.state IN %s)
            AND (account_account.account_type IN %s)
            AND (COALESCE(l.date_maturity,l.date) >= %s)\
            AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
        AND (l.date <= %s)
        AND l.company_id IN %s'''
        cr.execute(query, (
            tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            if partner_id not in paid_amounts:
                paid_amounts[partner_id] = 0.0
            line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)
            line_balance_amount = 0
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency,
                                                        partial_line.amount)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency,
                                                        partial_line.amount)
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        history_pdc_payment_amt = []
        account_ids = []
        for i in range(range_count):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids))
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.account_type IN %s)
                AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND ''' + dates_query + '''
            AND (l.date <= %s)
            AND l.company_id IN %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            partners_pdc_amount = {}
            partners_paid_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            move_line_ids = self.env['account.move.line'].browse(aml_ids)
            account_ids = move_line_ids.mapped('account_id')
            for line in move_line_ids:
                partner_id = line.partner_id.id or False

                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                    partners_pdc_amount[partner_id] = 0.0
                    partners_paid_amount[partner_id] = 0.0
                line_amount = ResCurrency._compute(line.company_id.currency_id, user_currency, line.balance)

                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:

                    if partial_line.max_date <= date_from:
                        line_amount += ResCurrency._compute(partial_line.company_id.currency_id, user_currency,
                                                            partial_line.amount)

                for partial_line in line.matched_credit_ids:

                    if partial_line.max_date <= date_from:
                        line_amount -= ResCurrency._compute(partial_line.company_id.currency_id, user_currency,
                                                            partial_line.amount)

                payment_obj = self.env['account.move']

                payment_lines = self.env['account.move.line'].search(
                    [('partner_id', '=', partner_id), ('move_id.date', '<=', date_from),
                     ('move_id.company_id', 'in', tuple(company_ids)),
                     ])
                paid_payment_lines = payment_obj.search(
                    [('partner_id', '=', partner_id), ('date', '<=', date_from), ('state', '=', 'posted'),
                     ('company_id', 'in', tuple(company_ids))])

                line_balance_amount = 0
                for rec in payment_lines:
                    line_balance_amount = float_repr(abs(rec.price_subtotal),
                                                     rec.move_id.currency_id.decimal_places if rec.move_id.currency_id else 2)
                line_pdc_amount = sum(payment.total_pdc_payment for payment in paid_payment_lines)
                partners_pdc_amount[partner_id] = float(line_balance_amount)
                line_balance_amount = 0
                partners_paid_amount[partner_id] = line_pdc_amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    partners_pdc_amount[partner_id] += line_balance_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })
            history.append(partners_amount)
            history_pdc_payment_amt.append(partners_paid_amount)

        for account in account_ids:
            for partner in partners:
                if partner['account_id'] == account.id:
                    if partner['partner_id'] is None:
                        partner['partner_id'] = False
                    at_least_one_amount = False
                    values = {}
                    undue_amt = 0.0
                    if partner[
                        'partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                        undue_amt = undue_amounts[partner['partner_id']]

                    total[range_count + 1] = total[range_count + 1] + undue_amt
                    values['direction'] = undue_amt
                    if not float_is_zero(values['direction'],
                                         precision_rounding=self.env.user.company_id.currency_id.rounding):
                        at_least_one_amount = True

                    line_balance_amount = 0
                    for i in range(range_count):
                        during = False
                        during_pdc = False
                        if partner['partner_id'] in history[i]:
                            during = [history[i][partner['partner_id']]]

                        if partner['partner_id'] in history_pdc_payment_amt[i]:
                            payment = [history_pdc_payment_amt[i][partner['partner_id']]]
                            pdc_payment_amt = (payment and payment[0] or 0)
                            values['pdc_payment_amt'] = pdc_payment_amt
                        if not 'pdc_payment_amt' in values.keys():
                            values['pdc_payment_amt'] = 0

                        # Adding counter
                        total[(i)] = total[(i)] + (during and during[0] or 0)
                        values[str(i)] = during and during[0] or 0.0
                        if not float_is_zero(values[str(i)],
                                             precision_rounding=self.env.user.company_id.currency_id.rounding):
                            at_least_one_amount = True
                    values['total'] = sum([values['direction']] + [values[str(i)] for i in range(range_count)])

                    ## Add for total
                    total[(i + 1)] += values['total']
                    values['partner_id'] = partner['partner_id']
                    values['net_balance'] = values['total'] - values['pdc_payment_amt']
                    if partner['partner_id']:
                        browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                        values['name'] = browsed_partner.name and len(
                            browsed_partner.name) >= 45 and browsed_partner.name[
                                                            0:40] + '...' or browsed_partner.name
                        if account_type[0] == 'asset_receivable':
                            values['payment_terms'] = sum(
                                term.days for term in browsed_partner.property_payment_term_id.line_ids)
                        else:
                            values['payment_terms'] = sum(
                                term.days for term in browsed_partner.property_supplier_payment_term_id.line_ids)
                        values['trust'] = browsed_partner.trust
                        values['range_count'] = range_count
                        values['customer_code'] = browsed_partner.customer_code
                        values['account_id'] = account.id
                        values['account_code'] = account.code
                        values['account_name'] = account.name
                        res.append(values)

        return res, total, lines, account_ids

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        total = []
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        company_id = data['form'].get('company_id')
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))

        if data['form']['result_selection'] == 'customer':
            account_type = ['asset_receivable']
        elif data['form']['result_selection'] == 'supplier':
            account_type = ['liability_payable']
        else:
            account_type = ['liability_payable', 'asset_receivable']

        movelines, total, dummy, account_ids = self._get_partner_move_lines(account_type, date_from,
                                                                            data['form'].get('period_length'),
                                                                            data['form'].get('period_length_months'),
                                                                            data['form'].get('period_length_type'),
                                                                            data['form']['un_even'],
                                                                            data['form'].get('period_length_uneven'),
                                                                            data)
        accounts = []
        lines = []
        for acc_id in account_ids:
            values = []
            vals = {
                'account_name': acc_id.name,
                'account_code': acc_id.code,
                'lines': [],
            }
            for move_li in movelines:
                if move_li['account_id'] == acc_id.id:
                    values.append(move_li)
            vals['lines'] = values
            lines.append(vals)

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_account_lines': lines,
            'get_direction': total,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
        }
