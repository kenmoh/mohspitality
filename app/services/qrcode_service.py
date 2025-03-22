from pathlib import Path
import zipfile
import qrcode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_models import QRCode, User
from app.schemas.room_schema import OutletType, QRCodeCreate, QRCodeResponse
from app.schemas.user_schema import UserType


# ================== QR CODE ================

async def create_qrcode(
    db: AsyncSession, current_user: User, qrcode_data: QRCodeCreate
) -> str:
    base_url: str = "https://mohspitality.com"
    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id

    rooms_list = [room.strip()
                  for room in qrcode_data.room_or_table_numbers.split(",")]
    rooms_set = set(rooms_list)
    unique_rooms = list(rooms_set)

    unique_rooms_string = ", ".join(sorted(rooms_set))

    # limits = supabase.table('qr_code_limit').select('*').execute()

    # qrcodes = supabase.table('qrcodes').select(
    #     '*').eq('company_id', current_user['company_id']).execute().count

    # print(limits, '==================', qrcodes)

    # limit = (
    #     limits[0]['basic'] if current_user['subscription_type'] == SubscriptionType.BASIC else
    #     limits[0]['premium'] if current_user['subscription_type'] == SubscriptionType.PREMIUM else
    #     limits[0]['enterprise'] if current_user['subscription_type'] == SubscriptionType.ENTERPRISE else
    #     limits[0]['trial'] if current_user['subscription_type'] == SubscriptionType.TRIAL else 0
    # )

    # if qrcodes >= limit:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
    #                         detail=f'Your plan have reached the maximum qr code generation limit of {limit}. Please upgrade')

    # Generate QR codes
    try:
        # Create temporary zip file
        temp_dir = Path("room-qrcodes")
        temp_dir.mkdir(exist_ok=True)

        zip_path = temp_dir / f"qrcodes-{company_id}.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_file:

            for room in unique_rooms:
                if qrcode_data.outlet_type == OutletType.ROOM_SERVICE:
                    room_table_url = (
                        f"""{base_url}/users/{company_id}?room={room}"""
                    )
                elif qrcode_data.outlet_type == OutletType.RESTAURANT:
                    room_table_url = f"""{base_url}/users/{company_id}?table={room}"""

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(room_table_url)
                qr.make(fit=True)

                qr_image = qr.make_image(
                    fill_color=qrcode_data.fill_color or "black",
                    back_color=qrcode_data.back_color or "white",
                )

                # Save QR code to temporary file
                temp_file = temp_dir / f"room_{room}.png"
                qr_image.save(temp_file)

                # Add to zip file
                zip_file.write(temp_file, f"room_{room}.png")

                # Clean up temporary file
                temp_file.unlink()

            qr_code = QRCode(
                company_id=company_id,
                room_or_table_numbers=unique_rooms_string,
                fill_color=qrcode_data.fill_color,
                back_color=qrcode_data.back_color,
                outlet_type=qrcode_data.outlet_type
            )
            db.add(qr_code)
            await db.commit()
            await db.refresh(qr_code)
            return str(zip_path)

    except Exception as e:
        # Clean up any remaining temporary files
        for file in temp_dir.glob("*"):
            file.unlink()
        raise Exception(f"Failed to generate QR codes: {str(e)}")


async def get_qrcode(db: AsyncSession, current_user: User) -> list[QRCodeResponse]:

    company_id = current_user.id if current_user.user_type == UserType.COMPANY else current_user.company_id
    stmt = select(QRCode).where(QRCode.company_id == company_id)
    result = await db.execute(stmt)
    qr_codes = result.all()

    return qr_codes
