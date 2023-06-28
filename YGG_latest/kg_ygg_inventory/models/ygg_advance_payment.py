from odoo import api, fields, models


class YggAdvancePayment(models.Model):
    _name = 'ygg.advance.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'

    product_id = fields.Many2one('product.product', string="Product")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    debit_acc_id = fields.Many2one('account.account', string="Debit Account")
    credit_acc_id = fields.Many2one('account.account', string="Credit Account", domain="[('account_type', '=', 'asset_cash')]")
    amount = fields.Monetary(string="Amount")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Cancelled')], string='Status', readonly=True, default='draft')

    move_id = fields.Many2one('account.move', copy=False)
    # balance = fields.Float(compute="_compute_balance_amount")
    #
    # def _compute_balance_amount(self):

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            rec.debit_acc_id = rec.partner_id.property_account_receivable_id.id

    def action_confirm(self):
        if self.product_id.inventory_category == 'issuance_prepaid':
            if self.env.company.currency_id != self.currency_id:
                amount = self.currency_id._convert(self.amount, self.env.company.currency_id, self.env.company, fields.Date.today())
            else:
                amount = self.amount
            commission = amount * self.product_id.unrealised_commission_per
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'date': fields.Datetime.today(),
                'journal_id': self.env.ref('kg_ygg_inventory.advance_payment_journal').id,
                'partner_id': self.partner_id.id,
                'adv_payment_id': self.id,
                'line_ids': [
                    (0, 0, {
                        'name': self.partner_id.name + '- ' + str(amount),
                        'partner_id': self.partner_id.id,
                        'account_id': self.debit_acc_id.id,
                        'debit': amount,
                        'currency_id': self.currency_id.id,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': self.partner_id.name + '- ' + str(amount),
                        'partner_id': self.partner_id.id,
                        'account_id': self.credit_acc_id.id,
                        'debit': 0.0,
                        'currency_id': self.currency_id.id,
                        'credit': amount,
                    }),
                    (0, 0, {
                        'name': self.partner_id.name + '- ' + str(amount),
                        'partner_id': self.partner_id.id,
                        'account_id': self.product_id.categ_id.property_stock_valuation_account_id.id,
                        'debit': amount,
                        'currency_id': self.currency_id.id,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': self.partner_id.name + '- ' + str(amount),
                        'partner_id': self.partner_id.id,
                        'account_id': self.env['ir.config_parameter'].sudo().get_param('commission_revenue_acc_id'),
                        'debit': 0.0,
                        'currency_id': self.currency_id.id,
                        'credit': amount - commission,
                    }),
                    (0, 0, {
                        'name': self.partner_id.name + '- ' + str(amount),
                        'partner_id': self.partner_id.id,
                        'account_id': self.env['ir.config_parameter'].sudo().get_param('unrealised_acc_id'),
                        'debit': 0.0,
                        'currency_id': self.currency_id.id,
                        'credit': commission,
                    }),
                ]
            })
            move.action_post()
            self.move_id = move.id
            self.write({'state': 'confirm'})

    def view_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', '=', self.move_id.id)],
            'context': "{'create': False}"
        }

