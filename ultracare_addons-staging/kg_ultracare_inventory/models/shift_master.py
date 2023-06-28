# -*- coding: utf-8 -*-
from odoo import fields,models,api,_
from odoo import tools
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError, AccessError
from odoo import api, fields, models, SUPERUSER_ID, _

class kg_shift_master(models.Model):
    _name ="kg.shift.master"

    start_time = fields.Float('Start')
    name = fields.Char('name')
    end_time = fields.Float('End')
    kg_note = fields.Text('Remarks',)
    prescent_threshold = fields.Float('Prescent Threshold',)
    start_am_pm = fields.Selection([('am', 'AM'),('pm', 'PM'),], string='Status',required="1",default='am')
    end_am_pm = fields.Selection([('am', 'AM'),('pm', 'PM'),], string='Status',required="1",default='am')