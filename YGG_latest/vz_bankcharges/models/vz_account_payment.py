from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import formatLang, format_date


class AccountPayment(models.Model):
    _inherit = "account.payment"

    vz_bank_charge = fields.Monetary(currency_field='currency_id')
    enable_charge = fields.Boolean(default=False)

    @api.onchange('journal_id')
    def _onchange_enable_charge(self):
        if self.journal_id.type == 'bank' and self.env.company.enable_bank_charges:
            self.enable_charge = True
        else:
            self.enable_charge = False

    def _synchronize_from_moves(self, changed_fields):
        # "overriden original function to add some condition for bank charge payments"
        for rec in self:
            if self.env.company.enable_bank_charges:
                if self._context.get('skip_account_move_synchronization'):
                    return

                for pay in self.with_context(skip_account_move_synchronization=True):
                    # After the migration to 14.0, the journal entry could be shared between the account.payment and the
                    # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
                    if pay.move_id.statement_line_id:
                        continue

                    move = pay.move_id
                    move_vals_to_write = {}
                    payment_vals_to_write = {}

                    if 'journal_id' in changed_fields:
                        if pay.journal_id.type not in ('bank', 'cash'):
                            raise UserError(_("A payment must always belongs to a bank or cash journal."))

                    if 'line_ids' in changed_fields:
                        all_lines = move.line_ids
                        liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                        if len(liquidity_lines) != 1 and not self.env.company.enable_bank_charges:
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must"
                                "include one and only one outstanding payments/receipts account.",
                                move.display_name,
                            ))

                        if len(counterpart_lines) != 1 and not self.env.company.enable_bank_charges:
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must"
                                "include one and only one receivable/payable account (with an exception of "
                                "internal transfers).",
                                move.display_name,
                            ))
                        if writeoff_lines and len(writeoff_lines.account_id) != 1 and not self.env.company.enable_bank_charges:
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, "
                                "all optional journal items must share the same account.",
                                move.display_name,
                            ))

                        if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must "
                                "share the same currency.",
                                move.display_name,
                            ))
                        """updated this warning message"""
                        if any(line.partner_id != all_lines[0].partner_id for line in
                               all_lines):
                            raise UserError(_(
                                "Journal Entry %s is not valid. In order to proceed, the journal items must "
                                "share the same partner.",
                                move.display_name,
                            ))

                        for line in liquidity_lines:
                            liquidity_amount = line.amount_currency

                        move_vals_to_write.update({
                            'currency_id': liquidity_lines.currency_id.id,
                            'partner_id': liquidity_lines.partner_id.id,
                        })
                        payment_vals_to_write.update({
                            'amount': abs(liquidity_amount),
                            'partner_type': 'customer',
                            'currency_id': liquidity_lines.currency_id.id,
                            'destination_account_id': counterpart_lines.account_id.id,
                            'partner_id': liquidity_lines.partner_id.id,
                        })
                        if liquidity_amount > 0.0:
                            payment_vals_to_write.update({'payment_type': 'inbound'})
                        elif liquidity_amount < 0.0:
                            payment_vals_to_write.update({'payment_type': 'outbound'})

                    move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
                    pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))
            else:
                return super(AccountPayment, self)._synchronize_from_moves(changed_fields)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        res = super()._prepare_move_line_default_vals(write_off_line_vals = write_off_line_vals)

        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
        write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.vz_bank_charge
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.vz_bank_charge
        else:
            liquidity_amount_currency = 0.0

        currency_id = self.currency_id.id

        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency

        # Compute a default label to set on the journal items.
        liquidity_line_name = ''.join(x[1] for x in self._get_bank_charge_label_name())

        sign = -1 if self.payment_type == 'outbound' else 1

        debit = {
            'name': liquidity_line_name,
            'date_maturity': self.date,
            'amount_currency': sign * liquidity_amount_currency,
            'currency_id': currency_id,
            'debit': self.vz_bank_charge,
            'credit': 0,
            'partner_id': self.partner_id.id,
            'account_id': self.journal_id.bank_charge_account.id,
        },
        # credit = {
        #     'name': liquidity_line_name,
        #     'date_maturity': self.date,
        #     'amount_currency': sign * counterpart_amount_currency,
        #     'currency_id': currency_id,
        #     'debit': 0,
        #     'credit': self.vz_bank_charge,
        #     'partner_id': self.partner_id.id,
        #     'account_id': self.destination_account_id.id,
        #
        # },


        if self.env.company.enable_bank_charges and self.enable_charge and self.vz_bank_charge:
            charge_list = []
            charge_list.extend(debit)
            for d in res:
                if d['account_id'] == self.destination_account_id.id:
                    d['amount_currency'] = d['amount_currency'] - sign * liquidity_amount_currency
                    d['credit'] = d['credit'] + self.vz_bank_charge

            # charge_list.extend(credit)
            charge_list.extend(res)
            res = charge_list
        print("res", res)

        return res


    def _get_bank_charge_label_name(self):
        self.ensure_one()
        values = [
            ('label', _("Bank Charges")),
            ('sep', ' '),
            ('amount', formatLang(self.env, self.vz_bank_charge, currency_obj=self.currency_id)),
        ]
        if self.ref:
            values += [
                ('sep', ' - '),
                ('partner', self.ref),
            ]
        return values
























