"""Veritabanı şemasını güncelleyen yardımcı script."""

from utils.db import db_cursor

def update_schema():
    """Mevcut veritabanı şemasını günceller."""
    
    print("Veritabanı şeması güncelleniyor...")
    
    # Yeni sütunları ekle
    with db_cursor() as cur:
        # 1. password_change_needed sütununu kontrol et ve yoksa ekle
        cur.execute("""
            SELECT COUNT(*) as count
            FROM information_schema.columns 
            WHERE table_schema = DATABASE()
            AND table_name = 'users' 
            AND column_name = 'password_change_needed'
        """)
        result = cur.fetchone()
        
        if result['count'] == 0:
            print("'password_change_needed' sütunu users tablosuna ekleniyor...")
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN password_change_needed TINYINT(1) DEFAULT 0
            """)
            print("Eklendi.")
        else:
            print("'password_change_needed' sütunu zaten mevcut.")
    
    print("Veritabanı şeması güncellemesi tamamlandı.")

if __name__ == "__main__":
    update_schema() 