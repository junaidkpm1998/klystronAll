# -*- coding: utf-8 -*-
from odoo import models, api, fields, _

# -*- coding: utf-8 -*-
from odoo import models, api, fields, tools, _
import math
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round
import re
from odoo.osv import expression
from collections import defaultdict


class product_template(models.Model):
    _inherit = 'product.template'

    # REORDERING RULE
    @api.depends('kg_reordering_value', 'product_variant_ids.stock_quant_ids',
                 'product_variant_ids.stock_move_ids', 'product_variant_ids.qty_available')
    def _get_warning_msg(self):
        for template in self:
            for pdt in template.product_variant_ids:
                if template.kg_reordering_value > pdt.qty_available:
                    template.kg_reorder_warning = True
                else:
                    template.kg_reorder_warning = False

    kg_reorder_warning = fields.Boolean('Reorder Warning', compute=_get_warning_msg, store="True")
    kg_reordering_value = fields.Float('Re.Order Quantity')
    supplier_barcode = fields.Char(string='Supplier Barcode')
    product_group = fields.Many2one('product.group', string='Product Group')
    product_sub_group = fields.Many2one('product.sub.group', string='Product Sub Group')
    product_brand = fields.Many2one('product.brand', string='Product Brand')

    ## Facial SKU

    pulls_count = fields.Float('Pulls/Sheet Count', default=1)

    tissue_per_pack = fields.Float('Tissue Per Pack', compute='compute_outer_packing', store=True)

    tissue_per_uom = fields.Float('Tissue Per UOM', compute='compute_outer_packing', store=True)

    is_it_bom_created = fields.Boolean('BOM Created')

    ##trkt sku

    tr_bale_qty = fields.Float('Bale Quantity', compute='compute_outer_packing', store=True)

    tr_sheet_count = fields.Integer('Sheet Count')

    ##table napkin

    # tn_item_code = fields.Char('TN Item Code')

    tn_cut_length = fields.Float('Cut Length(mm)')

    tn_sheets_pack = fields.Integer('Sheets/Pack', compute='compute_outer_packing', store=True)

    tn_weight = fields.Float('Weight(grams)', compute='compute_tn_wght')

    tn_weight_uom = fields.Float('Weight per UOM(grams)', compute='compute_tn_wght')

    tn_poly_film_pack = fields.Float('Poly Film Reqired Per Pack(grams')

    tn_poly_film_per_uom = fields.Char('Poly Film Per UOM(gram)', compute='comp_tn_poly', store=True)

    @api.constrains('default_code')
    def _check_product_code(self):
        for rec in self:
            if rec.default_code:
                if len(rec.default_code) != 15:
                    raise ValidationError('SKU code should be 15 digits')

    @api.depends('tn_poly_film_pack', 'outer_packing_conf', 'tn_sheets_pack')
    def comp_tn_poly(self):
        for record in self:
            if record.tn_sheets_pack > 0:
                val = (record.tn_poly_film_pack) * float(record.outer_packing_conf) / (record.tn_sheets_pack)
                record.tn_poly_film_per_uom = val

    # poly_bag_per_uom = fields.Char('Poly Bag Per UOM(grams)')

    @api.depends('kg_ply', 'tn_cut_length', 'kg_width', 'kg_gsm', 'outer_packing_conf')
    def compute_tn_wght(self):
        for record in self:
            val = float(record.kg_ply) * (record.tn_cut_length) * float(record.kg_width) * float(record.kg_gsm)
            record.tn_weight = val / (1000.0 * 1000.0)
            record.tn_weight_uom = (val / (1000.0 * 1000.0)) * float(record.outer_packing_conf)

    tn_actual_speed = fields.Float('Actual Speed(m/min)', compute='compute_tn_act_speed')

    tn_prod_packs = fields.Float('Production(Packs/Min', compute='compute_tn_prod_packs')

    @api.depends('kg_machine', 'tn_cut_length')
    def compute_tn_act_speed(self):
        for record in self:
            mach_speed = record.kg_machine.kg_speed_m_min
            length = record.tn_cut_length
            val = 0
            if length > 0:
                val = (mach_speed * 1000.0) / length

            record.tn_actual_speed = val

    @api.depends('tn_actual_speed', 'tn_sheets_pack')
    def compute_tn_prod_packs(self):
        for record in self:
            act_speed = record.tn_actual_speed
            sheet = record.tn_sheets_pack
            val = 0
            if sheet > 0:
                val = act_speed / sheet
            record.tn_prod_packs = val

    kg_cust_id = fields.Many2one('res.partner', 'Customer')

    kg_supp_id = fields.Many2one('res.partner', 'Supplier')

    kg_cus_code = fields.Char('Customer Code')

    kg_sku_type = fields.Char('Product Type')
    kg_pack = fields.Many2one('kg.pack', 'Interfold pack')

    kg_core = fields.Many2one('kg.core', 'Core')

    kg_lbl = fields.Char('Label Application')

    kg_hndl = fields.Char('Handle Application')

    kg_emb = fields.Char('Embossing')

    kg_lam = fields.Char('Lamination')

    kg_width = fields.Char('Width(mm)')

    kg_perf = fields.Char('Perforation length(mm)')

    kg_dia = fields.Char('Diameter(mm)')

    kg_sht = fields.Char('Sheet Count', compute='compute_sheet_count')

    kg_ply = fields.Char('Plies')

    kg_gsm = fields.Char('GSM')

    kg_wght = fields.Char('Weight(grams)')

    kg_trrt = fields.Char('TRRT')

    kg_cph = fields.Char('CPH')

    cf_item_code = fields.Char('Item Code')

    cf_machine = fields.Char('Machine')

    # kg_product_type = fields.Many2one('kg.product.type','Product Type')

    inner_outer_pack_conf = fields.Char('Inner * Outer Packing Configuration ')

    outer_packing_conf = fields.Char('Outer Packing Configuration', compute='compute_outer_packing', store=True)

    kg_sleeve = fields.Char('Sleeve')

    kg_print = fields.Char('Print')

    kg_location = fields.Char('Location')

    @api.depends('inner_outer_pack_conf', 'pulls_count')
    def compute_outer_packing(self):
        for record in self:
            if record.inner_outer_pack_conf:
                if record.categ_id.name == 'Jumbo SKU':
                    check = (record.inner_outer_pack_conf).split('x')
                    if len(check) == 2:
                        if check[0] == '1' and check[1] == '1':
                            record.outer_packing_conf = 6
                        else:
                            record.outer_packing_conf = float(check[1]) * float(check[0])
                    else:
                        record.outer_packing_conf = 0
                elif record.categ_id.name == 'Facial SKU':
                    check = (record.inner_outer_pack_conf).split('x')
                    if len(check) == 2:
                        record.outer_packing_conf = float(check[1])
                        record.tissue_per_pack = float(check[0]) * record.pulls_count

                        record.tissue_per_uom = float(check[0]) * record.pulls_count * float(check[1])
                    else:
                        record.outer_packing_conf = 0
                elif record.categ_id.name == 'Table Napkin SKU' or record.categ_id.name == 'TR KT SKU':
                    check = (record.inner_outer_pack_conf).split('x')
                    if len(check) == 2 and (record.inner_outer_pack_conf) != 'x':
                        record.tn_sheets_pack = float(check[0])
                        record.outer_packing_conf = float(check[1]) * float(check[0])
                        record.tr_bale_qty = float(check[0])

    outer_pack_uom = fields.Char('Outer Pack/UOM')

    outer_carton_uom = fields.Char('Outer Carton/UOM')

    core_size_ply = fields.Char('Core size(mm)/Core Ply/Perforation')

    # label = fields.Char('Label')

    tr_weight_roll = fields.Float('Weight per Roll(grams)', compute='compute_weight_roll', store=True)

    @api.depends('kg_gsm', 'kg_ply', 'kg_width', 'kg_perf', 'tr_sheet_count')
    def compute_weight_roll(self):
        for record in self:
            if record.kg_gsm and record.kg_ply and record.kg_perf and record.kg_width and record.tr_sheet_count:
                val = (float(record.kg_gsm)) * (float(record.kg_ply)) * (float(record.kg_perf)) * (
                    float(record.kg_width)) * (record.tr_sheet_count)
                val = val / (1000.0 * 1000.0)
                record.tr_weight_roll = val

    weight_roll = fields.Float('Weight per Roll(grams)')
    price_per_piece = fields.Float('Price Per Piece')
    # weight_tissue = fields.Float('Weight per Tissue(grams)')
    defined_weight = fields.Float('Weight per Tissue(grams)', compute='compute_weight_tissue')

    @api.depends('kg_gsm', 'kg_ply', 'kg_width', 'kg_length')
    def compute_weight_tissue(self):
        for record in self:
            gsm = float(record.kg_gsm)
            ply = float(record.kg_ply)
            width = float(record.kg_width)
            length = float(record.kg_length)

            val = (gsm * ply * width * length) / (1000.0 * 1000.0)
            record.defined_weight = val

    weight_uom = fields.Float('Weight per UOM(grams)', compute='compute_weight_uom', store=True)

    @api.onchange('defined_weight')
    def onchange_def_wght(self):
        for record in self:
            record.weight_roll = record.defined_weight

    # @api.depends('weight_roll','outer_packing_conf','tr_weight_roll','tissue_per_pack')
    # def compute_weight_uom(self):
    # for record in self:
    # if record.categ_id.name == 'TR KT SKU':
    # if record.tr_weight_roll and record.outer_packing_conf:
    #   record.weight_uom = record.tr_weight_roll*float(record.outer_packing_conf)
    # elif record.categ_id.name == 'Facial SKU':
    # record.weight_uom = (record.weight_roll)*(record.tissue_per_pack)*float(record.outer_packing_conf)
    # else:
    #  if record.weight_roll and record.outer_packing_conf:
    #     record.weight_uom=record.weight_roll*float(record.outer_packing_conf)

    @api.depends('weight_roll', 'outer_packing_conf', 'tr_weight_roll', 'tissue_per_pack', 'kg_ply', 'tn_cut_length',
                 'kg_width', 'kg_gsm')
    def compute_weight_uom(self):
        for record in self:
            if record.categ_id.name == 'TR KT SKU':
                if record.tr_weight_roll and record.outer_packing_conf:
                    record.weight_uom = record.tr_weight_roll * float(record.outer_packing_conf)
            elif record.categ_id.name == 'Facial SKU':
                record.weight_uom = (record.weight_roll) * (record.tissue_per_pack) * float(record.outer_packing_conf)

            elif record.categ_id.name == 'Table Napkin SKU':
                val = float(record.kg_ply) * (record.tn_cut_length) * float(record.kg_width) * float(record.kg_gsm)
                record.weight_uom = (val / (1000.0 * 1000.0)) * float(record.outer_packing_conf)

            else:
                if record.weight_roll and record.outer_packing_conf:
                    record.weight_uom = record.weight_roll * float(record.outer_packing_conf)

    roll_sheet_uom = fields.Float('Rolls/Sheets per uom')

    product_length = fields.Float('Product Length', compute='compute_product_length', store=True)

    @api.depends('weight_roll', 'kg_width', 'kg_gsm', 'kg_ply')
    def compute_product_length(self):
        for record in self:
            if record.weight_roll and record.kg_width and record.kg_gsm and record.kg_ply:
                #  print self.kg_gsm,self.kg_ply,self.kg_width,self.weight_roll,'111111111111'
                deno = (float(record.kg_gsm) * float(record.kg_ply) * float(record.kg_width)) / 1000.0
                val = record.weight_roll / deno
                record.product_length = val

    @api.depends('kg_perf', 'product_length')
    def compute_sheet_count(self):
        for record in self:
            if record.kg_perf:
                perf = float(record.kg_perf)
                if perf > 0:
                    if record.product_length > 0:
                        val = (record.product_length) / ((perf) / 1000.0)
                    else:
                        val = 1
                else:
                    val = 1
            else:
                val = 1
            record.kg_sht = round(val)

    rm_width = fields.Float('RM Width(mm)')

    sch_shift_hours = fields.Char('Scheduled DT/Shift Hours')

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        for record in self:
            if record.categ_id.name == 'Table Napkin SKU':
                record.sch_shift_hours = "0.3"
                record.kg_emb = 'Napkin'
            elif record.categ_id.name == 'Jumbo SKU':
                record.sch_shift_hours = "0.7"
            elif record.categ_id.name == 'TR KT SKU':
                record.sch_shift_hours = "1.5"

    no_of_rolls_log = fields.Char('No of Rolls/Log', compute='compute_rolls_log', store=True)
    no_of_clips_log = fields.Char('No of Rolls/Log', compute='compute_rolls_log', store=True)

    @api.depends('rm_width', 'kg_width')
    def compute_rolls_log(self):
        for record in self:
            if record.rm_width and record.kg_width:
                width = float(record.kg_width)
                rm_wid = record.rm_width
                val = math.floor(rm_wid / width)
                record.no_of_rolls_log = int(val)
                record.no_of_clips_log = int(val)

    eff_speed = fields.Char('Effective Speed(m/min)')

    eff_pulls_minute = fields.Char('Effective Production(Pulls/Min)', compute='comp_eff_prd',
                                   compute_sudo=True, store=True)

    eff_prd = fields.Char('Effective Production(Log/Min)', compute='comp_eff_prd', compute_sudo=True)

    @api.depends('eff_speed', 'product_length', 'kg_machine', 'tr_sheet_count', 'kg_perf', 'no_of_clips_log',
                 'kg_length', 'pulls_count')
    def comp_eff_prd(self):
        for record in self:
            if record.categ_id.name == 'TR KT SKU':
                if record.tr_sheet_count and record.kg_perf:
                    if record.eff_speed:
                        speed = float(record.eff_speed) * 1000.0
                        val = speed / ((record.tr_sheet_count) * (float(record.kg_perf)))
                    elif record.kg_machine:
                        speed = ((record.kg_machine.kg_speed_m_min) * 1000.0) or 0
                        val = speed / ((record.tr_sheet_count) * (float(record.kg_perf)))
                    else:
                        val = 0
                else:
                    val = 0
                record.eff_prd = round(val, 2)
            elif record.categ_id.name == 'Facial SKU':
                val = 0
                if record.eff_speed:
                    speed = float(record.eff_speed)

                elif record.kg_machine:
                    speed = ((record.kg_machine.kg_speed_m_min)) or 0

                if float(record.kg_length) > 0:
                    den = (float(record.kg_length)) / 1000.0
                    val = (speed / den) * 2 * (float(record.no_of_clips_log))

                log_p_min = 0
                if record.pulls_count > 0 and float(record.no_of_clips_log) > 0:
                    log_p_min = val / ((record.pulls_count) * (float(record.no_of_clips_log)))

                record.eff_pulls_minute = round(val, 0)
                record.eff_prd = round(log_p_min, 2)

                # record.eff_prd = round(val,2)
            else:
                if record.product_length:
                    if record.eff_speed:
                        speed = float(record.eff_speed)
                        val = speed / record.product_length
                    elif record.kg_machine:
                        speed = record.kg_machine.kg_speed_m_min or 0
                        val = speed / record.product_length
                    else:
                        val = 0
                else:
                    val = 0
                record.eff_prd = round(val, 2)

    packs_per_min = fields.Float('Packs Per Minute', compute='comp_packs_min')

    @api.depends('eff_prd', 'no_of_clips_log', 'inner_outer_pack_conf')
    def comp_packs_min(self):
        for record in self:
            if record.inner_outer_pack_conf:
                check = (record.inner_outer_pack_conf).split('x')
                val = 0
                if len(check) == 2:
                    den = float(check[0])
                    if den > 0:
                        logs = float(record.eff_prd)
                        clips = float(record.no_of_clips_log)

                        val = (logs * clips) / den
            else:
                val = 0
            record.packs_per_min = round(val, 0)

    eff_speed_rolls = fields.Char('Rolls or Box Per Minute', compute='comp_eff_speed_rolls', store=True)

    @api.depends('eff_prd', 'no_of_rolls_log')
    def comp_eff_speed_rolls(self):
        for record in self:
            if record.eff_prd and record.no_of_rolls_log:
                prd = float(record.eff_prd)
                rolls = float(record.no_of_rolls_log)
                val = prd * rolls
                record.eff_speed_rolls = round(val, 0)

    eff_output_carton = fields.Char('Effective Output(Cartons/Hour)', compute='comp_eff_car_hour')

    @api.depends('eff_output_car_shift')
    def comp_eff_car_hour(self):
        for record in self:
            if record.eff_output_car_shift:
                act_conf = self.env['kg.prod.conf'].search([('active', '=', True)])
                if not act_conf:
                    raise UserError(_('Create Active Production Configuration'))
                speed = float(record.eff_output_car_shift)
                if act_conf.kg_shift_hours:
                    record.eff_output_carton = round(speed / (act_conf.kg_shift_hours))
                else:
                    record.eff_output_carton = 0

    eff_output_car_shift = fields.Char('Effective Output(Carton/Shift)', compute='comp_car_shift')

    @api.depends('packs_per_min', 'eff_speed_rolls', 'effic', 'sch_shift_hours', 'outer_packing_conf',
                 'tn_actual_speed')
    def comp_car_shift(self):
        for record in self:
            if record.categ_id.name != 'Table Napkin SKU' and record.categ_id.name != 'Facial SKU':
                if record.eff_speed_rolls and record.sch_shift_hours and record.outer_packing_conf:
                    speed = float(record.eff_speed_rolls)
                    act_conf = self.env['kg.prod.conf'].search([('active', '=', True)])
                    if not act_conf:
                        raise UserError(_('Create Active Production Configuration'))
                    if record.effic:
                        eff = float(record.effic)
                        first_val = speed * 60.0 * (eff / 100.0)
                    else:
                        first_val = speed * 60.0 * ((act_conf.kg_global_eff) / 100.0)
                    second_val = first_val * ((act_conf.kg_quality_rate) / 100.0)
                    tot_hrs = (act_conf.kg_shift_hours) - float(record.sch_shift_hours)
                    outer = float(record.outer_packing_conf)
                    if outer > 0:
                        final_val = (second_val * tot_hrs) / outer
                    else:
                        final_val = 0
                else:
                    final_val = 0
                record.eff_output_car_shift = round(final_val)

            elif record.categ_id.name == 'Facial SKU':
                if record.packs_per_min and record.sch_shift_hours and record.outer_packing_conf:
                    speed = float(record.packs_per_min)
                    act_conf = self.env['kg.prod.conf'].search([('active', '=', True)])
                    if not act_conf:
                        raise UserError(_('Create Active Production Configuration'))

                    if record.effic:
                        eff = float(record.effic)

                        first_val = speed * 60.0 * (eff / 100.0)

                    else:
                        first_val = speed * 60.0 * ((act_conf.kg_global_eff) / 100.0)

                    second_val = first_val * ((act_conf.kg_quality_rate) / 100.0)

                    tot_hrs = (act_conf.kg_shift_hours) - float(record.sch_shift_hours)

                    outer = float(record.outer_packing_conf)

                    if outer > 0:

                        final_val = (second_val * tot_hrs) / outer
                    else:
                        final_val = 0

                else:
                    final_val = 0

                record.eff_output_car_shift = round(final_val)
            elif record.categ_id.name == 'Table Napkin SKU':
                if record.tn_actual_speed and record.sch_shift_hours and record.outer_packing_conf:
                    speed = float(record.tn_actual_speed)
                    act_conf = self.env['kg.prod.conf'].search([('active', '=', True)])
                    if not act_conf:
                        raise UserError(_('Create Active Production Configuration'))

                    if record.effic:
                        eff = float(record.effic)

                        first_val = speed * 60.0 * (eff / 100.0)

                    else:
                        first_val = speed * 60.0 * ((act_conf.kg_global_eff) / 100.0)

                    second_val = first_val * ((act_conf.kg_quality_rate) / 100.0)

                    tot_hrs = (act_conf.kg_shift_hours) - float(record.sch_shift_hours)

                    outer = float(record.outer_packing_conf)

                    if outer > 0:

                        final_val = (second_val * tot_hrs) / outer
                    else:
                        final_val = 0

                else:
                    final_val = 0

                record.eff_output_car_shift = round(final_val)

    eff_output_car_month = fields.Char('Effective Output(Cartons/Month)', compute='comp_eff_month')

    @api.depends('eff_output_car_shift')
    def comp_eff_month(self):
        for record in self:
            if record.eff_output_car_shift:
                act_conf = self.env['kg.prod.conf'].search([('active', '=', True)])
                if not act_conf:
                    raise UserError(_('Create Active Production Configuration'))
                speed = float(record.eff_output_car_shift)

                val = speed * (act_conf.kg_no_of_shifts) * (act_conf.kg_after_main)


            else:
                val = 0
            record.eff_output_car_month = val

    eff_ton_per_month = fields.Char('Effective Tonnage per Month', compute='comp_eff_ton', store=True)

    @api.depends('eff_output_car_month', 'outer_packing_conf', 'weight_roll', 'tn_cut_length', 'kg_width', 'kg_ply',
                 'kg_gsm', 'tr_sheet_count', 'kg_perf', 'weight_uom')
    def comp_eff_ton(self):
        for record in self:
            if record.categ_id.name == 'Jumbo SKU':
                if record.eff_output_car_month and record.outer_packing_conf and record.weight_roll:
                    car_month = float(record.eff_output_car_month)
                    outer = float(record.outer_packing_conf)
                    val = (car_month * outer * (record.weight_roll)) / (1000.0 * 1000.0)
                else:
                    val = 0
                record.eff_ton_per_month = round(val)
            elif record.categ_id.name == 'Facial SKU':
                if record.eff_output_car_month and record.weight_uom:
                    mon = float(record.eff_output_car_month)
                    uom = float(record.weight_uom)

                    val = (mon * uom) / (1000.0 * 1000.0)
                else:
                    val = 0
                record.eff_ton_per_month = round(val)
            elif record.categ_id.name == 'Table Napkin SKU':
                val = float(record.eff_output_car_month) * float(record.outer_packing_conf) * float(
                    record.tn_cut_length) * float(record.kg_width) * float(record.kg_ply) * float(record.kg_gsm)
                record.eff_ton_per_month = round(val / (1000.0 * 1000.0 * 1000.0 * 1000.0))
            elif record.categ_id.name == 'TR KT SKU':
                val = float(record.eff_output_car_month) * float(record.outer_packing_conf) * float(
                    record.tr_sheet_count) * float(record.kg_perf) * float(record.kg_width) * float(
                    record.kg_ply) * float(record.kg_gsm)
                record.eff_ton_per_month = round(val / (1000.0 * 1000.0 * 1000.0 * 1000.0))

    pack_mach_speed = fields.Char('Packing Machine Speed(Packs/Minute)', default="70.0")

    poly_film_per_uom = fields.Char('Poly Film Per UOM(gram)')

    poly_bag_per_uom = fields.Char('Poly Bag Per UOM(grams)')

    effic = fields.Char('Efficiency(%)')

    bale_qty_rolls = fields.Char('Bale Quantity(Rolls)')

    poly_film_per_bale = fields.Char('Poly Film Per Bale(grams)')

    cut_length = fields.Char('Cut Length(mm)')

    sheets_per_pack = fields.Char('Sheets/Pack')

    production_packs_min = fields.Char('Production(Packs/Min)')

    actual_speed_napkins_min = fields.Char('Actual Speed(Napkins/Min)')

    poly_film_per_pack = fields.Char('Poly Film Per Pack(gram)')

    kg_length = fields.Char('Length(mm)')

    kg_pulls_count = fields.Char('Pulls Count')

    effec_shift_hours = fields.Char('Effective Shift Hours')

    main_mach_speed = fields.Char('Main Machine Speed(m/Min)')

    no_of_clips_log = fields.Char('No of Clips/Log')

    paper_req_tonnes = fields.Char('Paper Required Tonnes')

    rm_type = fields.Char('RM Type')

    micron = fields.Char('Micron')

    eye_mark = fields.Char('Eye Mark(mm)')

    carton_size = fields.Char('Carton Size(L*B*H)')

    rm_desc = fields.Char('RM Description')

    standard_qty = fields.Float('Standard Qty')

    kg_internal_type = fields.Selection(
        [('finish', 'Finished Product'), ('spare', 'Spare Parts'), ('raw', 'Raw Materials'),
         ('service', 'Service Products'), ('misc', 'Miscellaneous'), ('trading', 'Trading Products')],
        'Kind of Product', required=True, default='misc')
    is_dummy_prod = fields.Boolean(string="Dummy Product")
    jumbo_roll = fields.Boolean(string="Jumbo Roll", default=False)

    kg_machine = fields.Many2one('kg.machine', 'Machine')

    kg_prod_cap_per_hour = fields.Float('Production Capacity in One Hour')

    kg_product_raw_lines = fields.One2many('kg.raw.material', 'material_product_id', 'Raw Materials')

    ###Spare Parts

    size_dim = fields.Char('Size/Dim')

    spare_item_code = fields.Char('Item Code')

    @api.onchange('spare_item_code')
    def onchange_spare_item_code(self):
        for record in self:
            if record.spare_item_code:
                record.default_code = record.spare_item_code

    spare_cc = fields.Char('CC', compute='compute_cc', store=True)

    @api.depends('kg_machine')
    def compute_cc(self):
        if self.kg_machine:
            self.spare_cc = self.kg_machine.name

    spare_type = fields.Many2one('kg.spare.type', 'Type')

    brand_make = fields.Char('Brand/Make')

    model_no = fields.Char('Model Number')

    spare_cat = fields.Many2one('kg.spare.cat', 'CAT')

    def correct_spare_code(self):
        for mach in self.env['kg.machine'].search([]):
            for spare_type in self.env['kg.spare.type'].search([]):
                i = 0
                for record in self.search([('kg_internal_type', '=', 'spare'), ('spare_type', '=', spare_type.id),
                                           ('kg_machine', '=', mach.id)]):
                    i = i + 1
                    count = str(i)
                    count = count.zfill(3)
                    record.write({'spare_code': count})

    @api.onchange('spare_type')
    def onchange_spare_type(self):
        for record in self:
            if record.spare_type:
                count = self.search_count(
                    [('kg_internal_type', '=', 'spare'), ('spare_type', '=', record.spare_type.id),
                     ('kg_machine', '=', record.kg_machine.id)]) or 0
                count = str(count + 1)
                count = count.zfill(3)
                record.spare_code = count

    @api.depends('spare_type')
    def comp_spare_count(self):
        for record in self:
            if record.spare_type:
                count = self.search_count(
                    [('kg_internal_type', '=', 'spare'), ('spare_type', '=', record.spare_type.id),
                     ('kg_machine', '=', record.kg_machine.id)]) or 0
                count = str(count)
                count = count.zfill(3)
                record.spare_count_value = count

    spare_code = fields.Char('SR. Code')

    # @api.onchange('spare_code')
    # def onchange_spare_code(self):
    #     if self.spare_code:
    #         self.spare_code = (self.spare_code).zfill(3)
    #
    spare_min_stk = fields.Float('Min STK')

    spare_rop = fields.Integer('ROP', compute='compute_rop')
    alternate_description = fields.Text('Alternate Description')
    invoice_description = fields.Text('Invoice Description')

    @api.depends('spare_min_stk')
    def compute_rop(self):
        for record in self:
            record.spare_rop = 0.6 * record.spare_min_stk

    spare_loc = fields.Char('LOC')
    spare_stat = fields.Char('STAT', compute='compute_spare_stat', search='search_spare_stat')

    database_stat = fields.Char('STAT')

    # def _search_product_values(self, operator, value,field):
    #     # TDE FIXME: should probably clean the search methods
    #     # to prevent sql injections
    #
    #     # if operator not in ('<', '>', '=', '!=', '<=', '>='):
    #     #     raise UserError(_('Invalid domain operator %s') % operator)
    #     # if not isinstance(value, (float, int)):
    #     #     raise UserError(_('Invalid domain right operand %s') % value)
    #
    #     # TODO: Still optimization possible when searching virtual quantities
    #     ids = []
    #     for product in self.search([]):
    #         if OPERATORS[operator](product[field], value):
    #             ids.append(product.id)
    #     return [('id', 'in', ids)]

    def search_spare_stat(self, operator, value):
        # TDE FIXME: should probably clean the search methods
        return [('database_stat', operator, value)]

    @api.depends('spare_rop', 'qty_available')
    def compute_spare_stat(self):
        for record in self:
            if record.qty_available >= record.spare_rop:
                record.spare_stat = 'Safe'
                record.write({'database_stat': 'Safe'})
            if record.qty_available < record.spare_rop:
                record.spare_stat = 'Procure'
                record.write({'database_stat': 'Procure'})

    spare_remarks = fields.Text('Remarks')

    spare_opening_stock_value = fields.Float('Opening Stock Value')

    spare_count_value = fields.Float('Count Value', compute='comp_spare_count', store=True)

    total = fields.Float(compute='_compute_total')

    @api.onchange('default_code')
    def onhcange_default_code(self):
        for record in self:
            record.barcode = record.default_code

    # @api.depends('spare_code', 'spare_type', 'spare_cc')
    # def _compute_spare_code(self):
    #     if self.spare_cc:
    #         a = self.spare_cat.code + self.spare_cc + '-' + self.spare_type.code + self.spare_code
    #         self.spare_item_code = a
    #         self.write({'default_code': a, 'barcode': a})
    #     else:
    #         self.spare_item_code = 0

    #     @api.onchange('spare_code','spare_type','spare_cc')
    #     def onchange_spare(self):
    #         print 'asssssssssssss'
    #         if self.spare_code and self.spare_type and self.spare_cc:
    #             print 'inside loop',self.spare_code,self.spare_type,self.spare_cc
    #             self.spare_item_code = '0'+self.spare_cc+'-'+self.spare_type.code+self.spare_code
    #

    ## Raw materials

    mat_type = fields.Many2one('kg.mat.type', 'Type')

    raw_remarks = fields.Text('Remarks')

    rm_desc = fields.Char('Description')

    rm_eye_mark = fields.Integer('Eye Mark(mm)')

    rm_micron = fields.Integer('Micron')

    rm_product_codes = fields.Char('Product Codes')

    rm_carton_size = fields.Char('Carton Size(LxBxH) mm')

    rm_standard_qty = fields.Char('Standard Qty')

    rm_length = fields.Float('Length(mm)')
    # alternate_description = fields.Char()
    # invoice_description = fields.Char()
    # rm_type = fields.Many2one('kg.rm.type','RM Type')
    stationary_consumed_qty = fields.Float(string="Consumed Qty", Store=True)
    rm_code = fields.Char('RM Code')

    @api.onchange('rm_code')
    def onchange_rm_code(self):
        for record in self:
            record.default_code = record.rm_code
            record.barcode = record.rm_code

    rm_width_mm = fields.Integer('Width(mm)')

    rm_gsm = fields.Float('GSM')

    rm_ply = fields.Integer('Ply')

    rm_product_type = fields.Char('Product Type')
    is_tracking = fields.Boolean('Is Tracking', default=False)

    @api.onchange('kg_internal_type')
    def onchange_internal_type(self):
        for record in self:
            if record.kg_internal_type == 'service':
                record.type = 'service'
            else:
                record.type = 'product'
            if record.kg_internal_type == 'finish':
                record.tracking = 'lot'
                record.is_tracking = True
            if record.kg_internal_type == 'spare' or record.kg_internal_type == 'misc' or record.kg_internal_type == 'trading' or record.kg_internal_type == 'service' or record.kg_internal_type == 'raw':
                record.tracking = 'none'
                record.is_tracking = False

    def action_open_material_consumption(self):
        return {
            'name': 'Stationary Consumption',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'stationary.consumption',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'target': 'new'
        }


class product_product(models.Model):
    _inherit = 'product.product'

    parent_member = fields.Char('Parent Member', default='MPI Products')
    supplier_barcode = fields.Char(string='Supplier Barcode')
    stationary_consumed_qty = fields.Float(string="Consumed Qty", Store=True)
    is_dummy_prod = fields.Boolean(string="Dummy Product")
    jumbo_roll = fields.Boolean(string="Jumbo Roll", default=False, related="product_tmpl_id.jumbo_roll")

    def action_open_material_consumption_product(self):
        return {
            'name': 'Stationary Consumption',
            'type': 'ir.actions.act_window',
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'stationary.consumption',
            'domain': [('product_id', '=', self.id)],
            'target': 'new'
        }

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(
                    self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(
                        self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(self._search([('supplier_barcode', '=', name)] + args, limit=limit,
                                                    access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(self._search([('detailed_type', '=', name)] + args, limit=limit,
                                                    access_rights_uid=name_get_uid))
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = list(self._search(args + [('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)],
                                                limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search([('default_code', '=', res.group(2))] + args, limit=limit,
                                                    access_rights_uid=name_get_uid))
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    ('partner_id', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit,
                                               access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return product_ids

    @api.onchange('kg_internal_type')
    def onchange_internal_type(self):
        for record in self:
            if record.kg_internal_type == 'service':
                record.type = 'service'
            else:
                record.type = 'product'

    # def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
    #     domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
    #     for i in domain_quant_loc:
    #         if len(i) == 3:
    #             if i[0] == 'location_id' and i[1] == 'child_of':
    #                 b = ('location_id.location_id', 'in', i[2])
    #                 domain_quant_loc.remove(i)
    #                 domain_quant_loc.append(b)
    #
    #     domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
    #     dates_in_the_past = False
    #     if to_date and to_date < fields.Datetime.now():  # Only to_date as to_date will correspond to qty_available
    #         dates_in_the_past = True
    #
    #     domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
    #     domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
    #     if lot_id:
    #         domain_quant += [('lot_id', '=', lot_id)]
    #     if owner_id:
    #         domain_quant += [('owner_id', '=', owner_id)]
    #         domain_move_in += [('restrict_partner_id', '=', owner_id)]
    #         domain_move_out += [('restrict_partner_id', '=', owner_id)]
    #     if package_id:
    #         domain_quant += [('package_id', '=', package_id)]
    #     if dates_in_the_past:
    #         domain_move_in_done = list(domain_move_in)
    #         domain_move_out_done = list(domain_move_out)
    #     if from_date:
    #         domain_move_in += [('date', '>=', from_date)]
    #         domain_move_out += [('date', '>=', from_date)]
    #     if to_date:
    #         domain_move_in += [('date', '<=', to_date)]
    #         domain_move_out += [('date', '<=', to_date)]
    #
    #     Move = self.env['stock.move']
    #     Quant = self.env['stock.quant']
    #     domain_move_in_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_in
    #     domain_move_out_todo = [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_move_out
    #     moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in
    #                         Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'],
    #                                         orderby='id'))
    #     moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in
    #                          Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'],
    #                                          orderby='id'))
    #
    #     # c =Quant.read_group(domain_quant, ['product_id', 'qty'], ['product_id'])
    #     # print c,'4444444444444,',domain_quant
    #     #
    #     # print Quant.search(domain_quant),'555555555'
    #     #
    #     # print Quant.search([('product_id','in',[5,6]),('location_id','child_of',[11])]),'6666666'
    #     quants_res = dict((item['product_id'][0], item['quantity']) for item in
    #                       Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
    #
    #     if dates_in_the_past:
    #         # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
    #         domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
    #         domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
    #         moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in
    #                                  Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'],
    #                                                  orderby='id'))
    #         moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in
    #                                   Move.read_group(domain_move_out_done, ['product_id', 'product_qty'],
    #                                                   ['product_id'], orderby='id'))
    #
    #     res = dict()
    #     for product in self.with_context(prefetch_fields=False):
    #         res[product.id] = {}
    #         if dates_in_the_past:
    #             qty_available = quants_res.get(product.id, 0.0) - moves_in_res_past.get(product.id,
    #                                                                                     0.0) + moves_out_res_past.get(
    #                 product.id, 0.0)
    #         else:
    #             qty_available = quants_res.get(product.id, 0.0)
    #         res[product.id]['qty_available'] = float_round(qty_available, precision_rounding=product.uom_id.rounding)
    #         res[product.id]['incoming_qty'] = float_round(moves_in_res.get(product.id, 0.0),
    #                                                       precision_rounding=product.uom_id.rounding)
    #         res[product.id]['outgoing_qty'] = float_round(moves_out_res.get(product.id, 0.0),
    #                                                       precision_rounding=product.uom_id.rounding)
    #         res[product.id]['virtual_available'] = float_round(
    #             qty_available + res[product.id]['incoming_qty'] - res[product.id]['outgoing_qty'],
    #             precision_rounding=product.uom_id.rounding)
    #
    #     return res
