@api.onchange('start_date', 'end_date', 'number_of_travellers', 'facilities_ids', 'vehicle_type')
def vehicle_name(self):
    # self.vehicle_id = False

    for rec in self:
        bookings = rec.search([
            ('start_date', '<', rec.end_date),
            ('end_date', '>', rec.start_date),
        ])
        vehicle_ids = bookings.mapped('vehicle_id')
        if rec.facilities_ids:
            return {
                'domain': {'vehicle_id': [
                    ('id', 'not in', vehicle_ids.ids),
                    ('facilities_ids', 'in', rec.facilities_ids.ids),
                    ('vehicle_types', 'like', rec.vehicle_type),
                    ('number_of_seats', '>=', rec.number_of_travellers),
                ],
                }
            }
        else:
            return {
                'domain': {'vehicle_id': [
                    ('id', 'not in', vehicle_ids.ids),
                    ('vehicle_types', 'ilike', rec.vehicle_type),
                    ('number_of_seats', '>', rec.number_of_travellers),
                ],
                }
            }
