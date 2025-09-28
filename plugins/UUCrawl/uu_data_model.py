class MarketModel:
    name = ''
    min_price = 0
    on_sale_count = 0
    on_lease_count = 0
    lease_unit_price = 0
    long_lease_unit_price = 0
    lease_deposit = 0

    def __init__(self,
                 name='',
                 min_price=0,
                 on_sale_count=0,
                 on_lease_count=0,
                 lease_unit_price=0,
                 long_lease_unit_price=0,
                 lease_deposit=0
                 ):
        self.name = name
        self.min_price = min_price
        self.on_sale_count = on_sale_count
        self.on_lease_count = on_lease_count
        self.lease_unit_price = lease_unit_price
        self.long_lease_unit_price = long_lease_unit_price
        self.lease_deposit = lease_deposit
