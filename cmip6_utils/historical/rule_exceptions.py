class HistoricalSimExceptions:
    @classmethod
    def check_ignore(cls):
        pass


# class BaseIngoreStartDate:
#     @classmethod
#     def check_ignore(cls):
#         pass


class EC_Earth3_historical_start_year_1970(HistoricalSimExceptions):
    # These variants start in 1970
    variants = [
        "r128i1p1f1",
        "r126i1p1f1",
        "r125i1p1f1",
        "r144i1p1f1",
        "r118i1p1f1",
        "r123i1p1f1",
        "r113i1p1f1",
        "r129i1p1f1",
        "r130i1p1f1",
        "r105i1p1f1",
        "r148i1p1f1",
        "r106i1p1f1",
        "r127i1p1f1",
        "r139i1p1f1",
        "r131i1p1f1",
        "r145i1p1f1",
        "r137i1p1f1",
        "r122i1p1f1",
        "r109i1p1f1",
        "r135i1p1f1",
        "r132i1p1f1",
        "r120i1p1f1",
        "r104i1p1f1",
        "r147i1p1f1",
        "r121i1p1f1",
        "r140i1p1f1",
        "r124i1p1f1",
        "r138i1p1f1",
        "r114i1p1f1",
        "r115i1p1f1",
        "r141i1p1f1",
        "r110i1p1f1",
        "r117i1p1f1",
        "r116i1p1f1",
        "r149i1p1f1",
        "r108i1p1f1",
        "r146i1p1f1",
        "r107i1p1f1",
        "r136i1p1f1",
        "r150i1p1f1",
        "r119i1p1f1",
        "r103i1p1f1",
        "r101i1p1f1",
        "r112i1p1f1",
        "r134i1p1f1",
        "r143i1p1f1",
        "r102i1p1f1",
        "r111i1p1f1",
        "r133i1p1f1",
        "r142i1p1f1",
    ]

    @classmethod
    def check_ignore(cls, dataset):
        for variant in cls.variants:
            if variant in dataset:
                return True
