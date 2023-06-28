from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    unrealised_acc_id = fields.Many2one('account.account', string='Unrealised Commission')
    # preset_code_acc_id = fields.Many2one('account.account', string='Preset Code Panda AED')
    commission_revenue_acc_id = fields.Many2one('account.account', string='Commission Revenue')
    receivable_clearing_acc_id = fields.Many2one('account.account', string='Receivable Clearing')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        unrealised_acc_id = params.get_param('unrealised_acc_id', default=False)
        # preset_code_acc_id = params.get_param('preset_code_acc_id', default=False)
        commission_revenue_acc_id = params.get_param('commission_revenue_acc_id', default=False)
        receivable_clearing_acc_id = params.get_param('receivable_clearing_acc_id', default=False)
        res.update(
            unrealised_acc_id=int(unrealised_acc_id),
            # preset_code_acc_id=int(preset_code_acc_id),
            commission_revenue_acc_id=int(commission_revenue_acc_id),
            receivable_clearing_acc_id=int(receivable_clearing_acc_id),
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("unrealised_acc_id", self.unrealised_acc_id.id)
        # self.env['ir.config_parameter'].sudo().set_param("preset_code_acc_id", self.preset_code_acc_id.id)
        self.env['ir.config_parameter'].sudo().set_param("commission_revenue_acc_id", self.commission_revenue_acc_id.id)
        self.env['ir.config_parameter'].sudo().set_param("receivable_clearing_acc_id", self.receivable_clearing_acc_id.id)
        return res