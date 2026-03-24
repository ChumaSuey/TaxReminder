# [DEFUNCT] Este archivo se mantiene solo como referencia
# Las descripciones se actualizaron manualmente en la base de datos

from models import DatabaseManager

def update_table_descriptions():
    db = DatabaseManager('sqlite:///tax_reminder.db')
    
    with db.get_db() as session:
        # Actualizar first_fortnight
        first = session.query(TaxTable).filter_by(name='first_fortnight').first()
        if first:
            first.description = 'Impuestos del 1-15 del mes'
            print("Actualizada descripción de first_fortnight")
        
        # Actualizar second_fortnight
        second = session.query(TaxTable).filter_by(name='second_fortnight').first()
        if second:
            second.description = 'Impuestos del 16 a fin de mes'
            print("Actualizada descripción de second_fortnight")
        
        session.commit()
        print("¡Actualización completada!")

if __name__ == "__main__":
    from models import TaxTable
    update_table_descriptions()
