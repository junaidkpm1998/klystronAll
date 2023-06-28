# -*- coding: utf-8 -*-
from odoo import models, api, fields, _

# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class kg_pack(models.Model):
    _name = 'kg.pack'
    _description = 'Pack'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_gsm(models.Model):
    _name = 'kg.gsm'
    _description = 'GSM'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_core(models.Model):
    _name = 'kg.core'
    _description = 'Core'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_lbl(models.Model):
    _name = 'kg.lbl'
    _description = 'LBL'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_hndl(models.Model):
    _name = 'kg.hndl'
    _description = 'HNDL'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_emb(models.Model):
    _name = 'kg.emb'
    _description = 'Emb'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_lam(models.Model):
    _name = 'kg.lam'
    _description = 'Lam'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_width(models.Model):
    _name = 'kg.width'
    _description = 'Width'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_perf(models.Model):
    _name = 'kg.perf'
    _description = 'Perf'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_dia(models.Model):
    _name = 'kg.dia'
    _description = 'Diameter'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_sht(models.Model):
    _name = 'kg.sht'
    _description = 'Sht'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_ply(models.Model):
    _name = 'kg.ply'
    _description = 'Ply'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_gsm(models.Model):
    _name = 'kg.core'
    _description = 'Gsm'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_wght(models.Model):
    _name = 'kg.wght'
    _description = 'Weight'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_trrt(models.Model):
    _name = 'kg.trrt'
    _description = 'TRRT'

    name = fields.Char('Name')

    desc = fields.Char('Description')


class kg_cph(models.Model):
    _name = 'kg.cph'
    _description = 'Cph'

    name = fields.Char('Name')

    desc = fields.Char('Description')
