import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from app.models.weapon import Weapon


def seed_weapons():
    app = create_app()
    with app.app_context():
        weapons_seed = [
            {'weapon_code': 'SWORD', 'weapon_name_vi': 'Kiếm', 'weapon_name_en': 'Sword', 'display_order': 1},
            {'weapon_code': 'SPEAR', 'weapon_name_vi': 'Thương', 'weapon_name_en': 'Spear', 'display_order': 2},
            {'weapon_code': 'STAFF', 'weapon_name_vi': 'Côn', 'weapon_name_en': 'Staff', 'display_order': 3},
            {'weapon_code': 'HALBERD', 'weapon_name_vi': 'Kích', 'weapon_name_en': 'Halberd', 'display_order': 4},
        ]

        for w in weapons_seed:
            exists = Weapon.query.filter(
                (Weapon.weapon_code == w['weapon_code']) |
                (Weapon.weapon_name_vi == w['weapon_name_vi']) |
                (Weapon.weapon_name_en == w['weapon_name_en'])
            ).first()
            if not exists:
                db.session.add(Weapon(
                    weapon_code=w['weapon_code'],
                    weapon_name_vi=w['weapon_name_vi'],
                    weapon_name_en=w['weapon_name_en'],
                    display_order=w['display_order'],
                    is_active=True,
                ))
                print(f"✅ Thêm vũ khí: {w['weapon_name_vi']} ({w['weapon_name_en']})")
            else:
                print(f"ℹ️  Vũ khí đã tồn tại: {w['weapon_name_vi']}")

        db.session.commit()
        print("✅ SEED WEAPONS HOÀN TẤT!")


if __name__ == '__main__':
    seed_weapons()


