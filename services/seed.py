"""
Seed script for BikerZone demo data.
Run with: python -m services.seed
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base
from app.models import (
    Usuario, Cliente, Moto, OrdenServicio,
    HistorialEstado, Repuesto, Proveedor,
    OrdenCompra, OrdenCompraDetalle
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        print("[BikerZone] Creando datos demo...")

        # Usuarios
        admin = Usuario(
            nombre="Administrador",
            email=settings.ADMIN_EMAIL,
            password_hash=pwd_context.hash(settings.ADMIN_PASSWORD),
            rol="admin"
        )
        tecnico1 = Usuario(
            nombre="Carlos Mendez",
            email="tecnico1@bikerzone.com",
            password_hash=pwd_context.hash("tecnico123"),
            rol="tecnico"
        )
        tecnico2 = Usuario(
            nombre="Ana Rodriguez",
            email="tecnico2@bikerzone.com",
            password_hash=pwd_context.hash("tecnico123"),
            rol="tecnico"
        )
        db.add_all([admin, tecnico1, tecnico2])
        db.flush()

        # Proveedores
        proveedores = [
            Proveedor(nombre="Repuestos MX", contacto="Juan Perez", telefono="55512345", email="contacto@repuestomx.com"),
            Proveedor(nombre="MotoParts SA", contacto="Maria Lopez", telefono="55598765", email="ventas@motoparts.com"),
            Proveedor(nombre="Distribuidora Norte", contacto="Pedro Garcia", telefono="55545678", email="info@distribnorte.com"),
            Proveedor(nombre="Importadora Sureste", contacto="Laura Torres", telefono="55532165", email="ventas@importsureste.com"),
            Proveedor(nombre="Repuestos Express", contacto="Roberto Diaz", telefono="55578912", email="pedidos@repexpress.com"),
        ]
        db.add_all(proveedores)
        db.flush()

        # Repuestos
        repuestos_data = [
            ("REP-001", "Pastilla de Freno Delantera", "Pastilla ceramica universal", "Frenos", "Brembo", 5, 25, 180.00, 320.00),
            ("REP-002", "Pastilla de Freno Trasera", "Pastilla ceramica universal", "Frenos", "EBC", 3, 18, 150.00, 280.00),
            ("REP-003", "Disco de Freno Delantero 320mm", "Disco flotante", "Frenos", "Galfer", 2, 8, 850.00, 1450.00),
            ("REP-004", "Aceite Motor 10W-40 4T", "Sintetico 1 litro", "Aceites", "Motul", 10, 45, 120.00, 220.00),
            ("REP-005", "Filtro de Aceite", "Filtro universal", "Motor", "K&N", 8, 30, 85.00, 160.00),
            ("REP-006", "Bujia NGK CR8E", "Bujia estandar", "Motor", "NGK", 10, 40, 45.00, 95.00),
            ("REP-007", "Cadena 520H 120L", "Cadena reforzada", "Transmision", "RK", 3, 12, 450.00, 780.00),
            ("REP-008", "Piñon Delantero 15T", "Acero al carbono", "Transmision", "JT Sprockets", 4, 15, 180.00, 320.00),
            ("REP-009", "Piñon Trasero 45T", "Aluminio 7075", "Transmision", "Supersprox", 3, 10, 350.00, 620.00),
            ("REP-010", "Amortiguador Trasero", "Ajustable precarga", "Suspension", "YSS", 2, 5, 2200.00, 3800.00),
            ("REP-011", "Filtro Aire Unibiquers", "Filtro lavable", "Motor", "Unibiquers", 4, 14, 320.00, 580.00),
            ("REP-012", "Rueda Delantera 120/70-17", "Radial", "Llantas", "Pirelli", 2, 6, 1800.00, 2900.00),
            ("REP-013", "Rueda Trasera 180/55-17", "Radial", "Llantas", "Pirelli", 2, 5, 2100.00, 3400.00),
            ("REP-014", "Kit de Embrague", "Disco y muelle", "Transmision", "Vortex", 2, 7, 1200.00, 2100.00),
            ("REP-015", "Guia de Cadena", "Nylon reforzado", "Transmision", "DID", 5, 20, 180.00, 320.00),
            ("REP-016", "Manubrio Clip-On", "Aluminio 7075", "Carroceria", "Accel", 3, 8, 650.00, 1100.00),
            ("REP-017", "Espejo Retrovisor Universal", "Par de espejos", "Carroceria", "Domino", 6, 25, 120.00, 250.00),
            ("REP-018", "Luz LED Delantera", "Proyector 45W", "Electrico", "G4", 3, 10, 450.00, 780.00),
            ("REP-019", "Bateria 12V 9Ah", "Gel sellada", "Electrico", "YTZ", 4, 12, 650.00, 1100.00),
            ("REP-020", "Cable de Acelerador", "Universal 1.3m", "Electrico", "Venhill", 5, 18, 85.00, 160.00),
            ("REP-021", "Bomba de Freno Delantera", "Reconstruccion completa", "Frenos", "Nissin", 2, 4, 1800.00, 3200.00),
            ("REP-022", "Sensor O2", "Lambda universal", "Electrico", "NGK", 3, 8, 350.00, 620.00),
            ("REP-023", "Coolant Radiador", "Refrigerante 1L", "Motor", "Motul", 10, 35, 95.00, 170.00),
            ("REP-024", "Spray Penetrante 400ml", "Multiusos", "Varios", "WD-40", 8, 50, 65.00, 120.00),
            ("REP-025", "Grasa Cadena 400ml", "Spray blanco", "Varios", "Motul", 6, 30, 110.00, 200.00),
            ("REP-026", "Juego de Buje A-Kit", "Completo suspension delantera", "Suspension", "All Balls", 2, 6, 450.00, 780.00),
            ("REP-027", "Guarda Polvo Horquilla", "Par de guardas", "Suspension", "Tusk", 4, 12, 180.00, 320.00),
            ("REP-028", "Rines 17 Excel", "Par de rines negros", "Llantas", "Excel", 1, 3, 4500.00, 7200.00),
            ("REP-029", "Tornilleria Inox", "Kit completo 50 pzas", "Varios", "Pro-Bolt", 3, 15, 350.00, 620.00),
            ("REP-030", "Cubre Cuadro Carbono", "Tapa lateral derecha", "Carroceria", "Hot Bodies", 2, 4, 1200.00, 2100.00),
        ]

        repuestos = []
        for r in repuestos_data:
            rep = Repuesto(
                codigo=r[0], nombre=r[1], descripcion=r[2], categoria=r[3],
                marca=r[4], stock_minimo=r[5], stock_actual=r[6],
                stock_reservado=0,
                precio_compra=r[7], precio_venta=r[8]
            )
            repuestos.append(rep)
        db.add_all(repuestos)
        db.flush()

        # Clientes y Motos
        clientes_data = [
            ("Miguel Hernandez", "55511111", "miguel@email.com", "Calle Norte 123"),
            ("Sofia Ramirez", "55522222", "sofia@email.com", "Av. Reforma 456"),
            ("Diego Morales", "55533333", "diego@email.com", "Blvd. Sur 789"),
            ("Isabella Vargas", "55544444", "isabella@email.com", "Calle Oriente 321"),
            ("Mateo Castillo", "55555555", "mateo@email.com", "Av. Libertad 654"),
            ("Valentina Cruz", "55566666", "valentina@email.com", "Calle Poniente 987"),
            ("Santiago Reyes", "55577777", "santiago@email.com", "Blvd. Norte 147"),
            ("Camila Torres", "55588888", "camila@email.com", "Av. Central 258"),
            ("Nicolas Flores", "55599999", "nicolas@email.com", "Calle Sur 369"),
            ("Lucia Mendez", "55500000", "lucia@email.com", "Av. Universidad 741"),
        ]

        motos_data = [
            ("Honda", "CBR600RR", 2022, "ABC123", "Roja", 15000),
            ("Yamaha", "MT-07", 2023, "DEF456", "Azul", 8000),
            ("Kawasaki", "Ninja 400", 2021, "GHI789", "Verde", 22000),
            ("Suzuki", "GSX-R750", 2020, "JKL012", "Negra", 30000),
            ("Ducati", "Monster 821", 2023, "MNO345", "Roja", 5000),
            ("BMW", "R1250GS", 2022, "PQR678", "Blanca", 18000),
            ("KTM", "390 Duke", 2023, "STU901", "Naranja", 6000),
            ("Harley-Davidson", "Iron 883", 2021, "VWX234", "Negra", 25000),
            ("Triumph", "Street Triple", 2022, "YZA567", "Plata", 12000),
            ("Honda", "Africa Twin", 2023, "BCD890", "Azul", 10000),
            ("Yamaha", "YZF-R3", 2022, "EFG123", "Roja", 14000),
            ("Kawasaki", "Z900", 2021, "HIJ456", "Verde", 20000),
            ("Suzuki", "V-Strom 650", 2023, "KLM789", "Amarilla", 9000),
            ("Ducati", "Scrambler", 2022, "NOP012", "Blanca", 7000),
            ("BMW", "S1000RR", 2023, "QRS345", "Blanca/Azul", 4000),
        ]

        clientes = []
        motos = []
        for i, c in enumerate(clientes_data):
            cliente = Cliente(nombre=c[0], telefono=c[1], email=c[2], direccion=c[3])
            clientes.append(cliente)
            db.add(cliente)
            db.flush()

            m = motos_data[i] if i < len(motos_data) else motos_data[0]
            moto = Moto(
                client_id=cliente.id, marca=m[0], modelo=m[1],
                anio=m[2], placa=m[3], color=m[4], kilometraje=m[5]
            )
            motos.append(moto)
            db.add(moto)
        db.flush()

        # Ordenes de servicio
        estados_posibles = [
            ["received"], ["received", "diagnosed"], ["received", "diagnosed", "quote_sent"],
            ["received", "diagnosed", "quote_sent", "quote_approved", "in_progress", "repairing", "ready", "delivered"],
            ["received", "diagnosed", "quote_sent", "quote_approved", "in_progress", "repairing"],
            ["received", "diagnosed", "quote_sent", "quote_approved", "in_progress", "repairing", "ready"],
            ["received", "diagnosed", "quote_sent", "quote_rejected"],
        ]

        clientes_con_motos = list(zip(clientes, motos))
        ordenes = []
        for i in range(20):
            cliente, moto = random.choice(clientes_con_motos)
            tecnico = random.choice([tecnico1, tecnico2])
            estados = random.choice(estados_posibles)
            estado_actual = estados[-1]

            precio = random.choice([None, None, 800.00, 1200.00, 2500.00, 3500.00, 4800.00])
            presupuesto = random.choice([None, 1500.00, 2000.00, 3000.00, 4000.00, 5500.00])

            fallas = [
                "Frenos chirrian al frenar",
                "Motor hace ruido extraño en frio",
                "No enciende, bateria nueva",
                "Cadena floja y saltando",
                "Fuga de aceite en motor",
                "Suspension delantera suelta",
                "Cambio de aceite y filtros",
                "Reparacion de llanta trasera",
                "Servicio general 10000km",
                "Cable de clutch roto",
                "Luz de freno no funciona",
                "Ruidos en suspension trasera",
                "Cambio de pastillas de freno",
                "Motor sobrecalienta en transito",
                "Filtro de aire sucio",
                "Bujias gastadas",
                "Rines abollados",
                "Kit de cadena desgastado",
                "Bomba de freno fallando",
                "Sensor de temperatura falla",
            ]

            orden = OrdenServicio(
                codigo=f"BZ-2026-{(i+1):05d}",
                client_id=cliente.id,
                motorcycle_id=moto.id,
                technician_id=tecnico.id,
                falla_reportada=random.choice(fallas),
                estado=estado_actual,
                presupuesto=presupuesto,
                precio_final=precio if estado_actual == "delivered" else None,
                kilometraje_entrada=moto.kilometraje,
            )
            ordenes.append(orden)
            db.add(orden)
            db.flush()

            # Historial
            for idx, estado in enumerate(estados):
                hist = HistorialEstado(
                    service_order_id=orden.id,
                    estado=estado,
                    user_id=tecnico.id,
                    observaciones=f"Estado cambiado a {estado}",
                    fecha=datetime.utcnow() - timedelta(days=len(estados) - idx)
                )
                db.add(hist)
        db.flush()

        # Ordenes de compra
        for i in range(5):
            proveedor = proveedores[i]
            repuestos_seleccionados = random.sample(repuestos, 3)

            oc = OrdenCompra(
                codigo=f"OC-2026-{(i+1):05d}",
                supplier_id=proveedor.id,
                user_id=admin.id,
                estado=random.choice(["pending", "sent", "received"]),
                notas=f"Compra de repuestos a {proveedor.nombre}"
            )
            db.add(oc)
            db.flush()

            subtotal_total = 0
            for rep in repuestos_seleccionados:
                cantidad = random.randint(5, 20)
                sub = float(rep.precio_compra) * cantidad
                subtotal_total += sub
                detalle = OrdenCompraDetalle(
                    purchase_order_id=oc.id,
                    part_id=rep.id,
                    cantidad=cantidad,
                    precio_unitario=rep.precio_compra,
                    subtotal=sub
                )
                db.add(detalle)

            oc.subtotal = subtotal_total
            oc.iva = subtotal_total * 0.12
            oc.total = subtotal_total * 1.12
        db.flush()

        db.commit()
        print("[BikerZone] Datos demo creados exitosamente!")
        print(f"  - 3 usuarios (admin + 2 tecnicos)")
        print(f"  - 10 clientes con 15 motos")
        print(f"  - 20 ordenes de servicio")
        print(f"  - 30 repuestos en inventario")
        print(f"  - 5 proveedores")
        print(f"  - 5 ordenes de compra")


if __name__ == "__main__":
    seed()
