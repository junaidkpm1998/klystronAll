# -*- coding: utf-8 -*-

from odoo import fields, models


class GratuitySettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gratuity_account_id = fields.Many2one('account.account', string='Payment Expense Account',
                                        config_parameter='hr_gratuity_settlement.gratuity_account_id')
