def action_confirm(self):
    res = super(SaleOrder, self).action_confirm()
    invoice_lines = []
    for line in self.order_line:
        vals = {
            'name': line.name,
            'price_unit': line.price_unit,
            'quantity': line.product_uom_qty,
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom.id,
            'tax_ids': [(6, 0, line.tax_id.ids)],
            'sale_line_ids': [(6, 0, [line.id])],
        }
        invoice_lines.append((0, 0, vals))
    self.env['account.move'].create({
        'ref': self.client_order_ref,
        'move_type': 'out_invoice',
        'invoice_origin': self.name,
        'invoice_user_id': self.user_id.id,
        'partner_id': self.partner_invoice_id.id,
        'currency_id': self.pricelist_id.currency_id.id,
        'invoice_line_ids': invoice_lines
    })
    return res