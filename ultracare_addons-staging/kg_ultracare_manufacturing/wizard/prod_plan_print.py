from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp


class kg_prod_plan_print(models.TransientModel):
    
    _name='kg.prod.plan.print'
    _description = 'Prod Plan Print'
    
    # date_from = fields.Date('Date From')
    
    # date_to = fields.Date('Date To')

    production_plan_id = fields.Many2one('kg.prod.plan', 'Production Plan')

    machine_id = fields.Many2one('kg.machine','Machine')
    
    
    def print_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['machine_id','production_plan_id'])[0]
        data['form']['kg_start_date'] = self.production_plan_id.kg_start_date
        data['form']['kg_end_date'] = self.production_plan_id.kg_end_date
    #    used_context = self._build_contexts(data)
     #   data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self.env['report'].get_action(self, 'kg_metropolic.report_prodplan', data=data)