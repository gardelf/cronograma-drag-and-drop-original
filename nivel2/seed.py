VALUES = [('experiencial','Experiencial',True),('hedonismo','Hedonismo',True),('creativo','Creativo',False),('responsabilidad','Responsabilidad',False),('actitudinal','Actitudinal',True)]
UNITS = [
 ('E01','experiencial','Trekking por la sierra','fixed','27',8,5,'Referencia pendiente: duración total o disfrute neto', [('Gasolina','12'),('Comida','15')]),
 ('E02','experiencial','Microteatro (3 obras)','fixed','17.50',6,2.5,'',[('Entradas','15'),('Gasolina','2.50')]),
 ('E03','experiencial','Volar avión de radiocontrol','fixed','6',5,3,'',[('Transporte','6')]),
 ('E04','experiencial','Concierto de música clásica','fixed','32.50',5,2,'',[('Entrada','30'),('Gasolina','2.50')]),
 ('E05','experiencial','Pádel en Rivas','fixed','15',5,2.5,'',[('Pista','10'),('Consumiciones','5')]),
 ('E06','experiencial','Pádel en El Estudiante','fixed','25',6,3,'',[('Gasolina','3'),('Pista','7'),('Cena','15')]),
 ('E07','experiencial','Clase particular de pádel','fixed','30',8,1,'',[('Clase','30')]),
 ('E08','experiencial','Esquiar en Baqueira con Cris','fixed','500',9,72,'Tres días completos; no equivale a tiempo neto de esquí',[]),
 ('H01','hedonismo','Cerveza Leffe y cena en cervecería','fixed','17',6,2.5,'',[]),
 ('H02','hedonismo','Comer pescado o pulpo con Cris en Maroma','fixed','30',6,2,'',[]),
 ('C01','creativo','Aeromodelismo y radiocontrol','variable',None,None,None,'',[]),
 ('C02','creativo','Desarrollo de la aplicación de gastos','variable',None,None,None,'',[]),
 ('C03','creativo','Construcción de la casa de Cercedilla','variable',None,None,None,'',[]),
 ('R01','responsabilidad','Piso Pedro Zerolo','variable',None,None,None,'',[]),
 ('R02','responsabilidad','Piso Playa Samil 4','variable',None,None,None,'',[]),
 ('R03','responsabilidad','Piso Playa Samil 8','variable',None,None,None,'',[]),
 ('R04','responsabilidad','Plaza de garaje 17','variable',None,None,None,'',[]),
 ('R05','responsabilidad','Plaza de garaje 39','variable',None,None,None,'',[]),
 ('R06','responsabilidad','Cartera de inversión','variable',None,None,None,'',[]),
 ('R07','responsabilidad','Salud','variable',None,None,None,'',[]),
]
def seed(cur):
    for row in VALUES:
        cur.execute('INSERT INTO n2_values VALUES (%s,%s,%s) ON CONFLICT DO NOTHING', row)
    for row in UNITS:
        cur.execute('INSERT INTO n2_units(id,value_code,name,cost_kind,standard_cost,satisfaction,hours,time_note) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id',row[:8])
        if cur.fetchone():
            for name,cost in row[8]:
                cur.execute('INSERT INTO n2_components(unit_id,name,cost) VALUES (%s,%s,%s)',(row[0],name,cost))
