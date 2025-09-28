from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from models.schema import PageStyle, AudienceType, SalesGoal

def get_main_menu(is_subscribed: bool = True) -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="🧠 تولید محتوا"))
    builder.add(KeyboardButton(text="🎛️ ویرایش پروفایل"))
    
    if is_subscribed:
        builder.add(KeyboardButton(text="📊 آمار استفاده"))
    else:
        builder.add(KeyboardButton(text="🔁 تمدید اشتراک"))
    
    builder.add(KeyboardButton(text="❓ راهنما"))
    builder.adjust(2, 2)
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="یک گزینه را انتخاب کنید..."
    )

def get_content_type_keyboard() -> ReplyKeyboardMarkup:
    """Content type selection keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="✍️ کپشن نویسی"))
    builder.add(KeyboardButton(text="🎬 سناریو ریلز"))
    builder.add(KeyboardButton(text="📷 ایده بصری"))
    builder.add(KeyboardButton(text="🔙 بازگشت"))
    
    builder.adjust(2, 2)
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="نوع محتوا را انتخاب کنید..."
    )

def get_discount_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for discount code flow"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔙 بازگشت"))
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="کد تخفیف را به صورت متن ارسال کنید..."
    )

def get_profile_setup_keyboard(step: str) -> InlineKeyboardMarkup:
    """Profile setup keyboard based on step"""
    builder = InlineKeyboardBuilder()
    
    if step == "style":
        for style in PageStyle:
            builder.add(InlineKeyboardButton(
                text=style.value,
                callback_data=f"style_{style.name.lower()}"
            ))
    elif step == "audience":
        for audience in AudienceType:
            builder.add(InlineKeyboardButton(
                text=audience.value,
                callback_data=f"audience_{audience.name.lower()}"
            ))
    elif step == "goal":
        for goal in SalesGoal:
            builder.add(InlineKeyboardButton(
                text=goal.value,
                callback_data=f"goal_{goal.name.lower()}"
            ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_profile_edit_keyboard() -> ReplyKeyboardMarkup:
    """Profile editing keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="🎨 تغییر سبک"))
    builder.add(KeyboardButton(text="👥 تغییر مخاطب"))
    builder.add(KeyboardButton(text="🎯 تغییر هدف"))
    builder.add(KeyboardButton(text="🏪 اطلاعات کسب‌وکار"))
    builder.add(KeyboardButton(text="🔙 بازگشت"))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="بخش مورد نظر را انتخاب کنید..."
    )

def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Payment options keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="💳 پرداخت ماهانه - 980,000 تومان",
        callback_data="payment_monthly_980000"
    ))
    builder.add(InlineKeyboardButton(
        text="💰 پرداخت فصلی - 7,599,000 تومان",
        callback_data="payment_seasonal_7599000"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Simple back keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔙 بازگشت"))
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="پیام خود را بنویسید یا بازگشت را انتخاب کنید..."
    )

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="✅ تایید", callback_data="confirm_yes"))
    builder.add(InlineKeyboardButton(text="❌ انصراف", callback_data="confirm_no"))
    
    builder.adjust(2)
    return builder.as_markup()

def get_confirmation_payment_keyboard() -> InlineKeyboardMarkup:
    """Confirmation payment keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(text="چرا که نه 🤗", callback_data="now"))
    builder.add(InlineKeyboardButton(text="بعدا 😮‍💨", callback_data="later"))
    
    builder.adjust(2)
    return builder.as_markup()

def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Initial start keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="آماده‌ام"))
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="روی آماده‌ام کلیک کنید..."
    )

def get_onboarding_keyboard(keyboard_type: str) -> ReplyKeyboardMarkup:
    """Dynamic onboarding keyboards"""
    builder = ReplyKeyboardBuilder()
    
    if keyboard_type == "skip":
        builder.add(KeyboardButton(text="رد کردن"))
        builder.add(KeyboardButton(text="🔙 بازگشت"))
        builder.adjust(1, 1)
    elif keyboard_type == "yes_no":
        builder.add(KeyboardButton(text="آره"))
        builder.add(KeyboardButton(text="نه"))
        builder.add(KeyboardButton(text="🔙 بازگشت"))
        builder.adjust(2, 1)
    elif keyboard_type == "continue":
        builder.add(KeyboardButton(text="ادامه بدیم"))
        builder.add(KeyboardButton(text="🔙 بازگشت"))
        builder.adjust(1, 1)
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="گزینه مورد نظر را انتخاب کنید..."
    )

def get_main_menu(is_subscribed: bool = True) -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="🧠 تولید محتوا"))
    builder.add(KeyboardButton(text="🎛️ ویرایش پروفایل"))
    
    if is_subscribed:
        builder.add(KeyboardButton(text="📊 آمار استفاده"))
        builder.add(KeyboardButton(text="🎁 کد تخفیف"))
    else:
        builder.add(KeyboardButton(text="🔁 تمدید اشتراک"))
        builder.add(KeyboardButton(text="🎁 کد تخفیف"))
    
    builder.add(KeyboardButton(text="❓ راهنما"))
    builder.add(KeyboardButton(text="👥 دعوت از دوستان"))
    
    builder.adjust(2, 2, 2)
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="یک گزینه را انتخاب کنید..."
    )

def get_content_type_keyboard() -> ReplyKeyboardMarkup:
    """Content type selection keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="✍️ کپشن نویسی"))
    builder.add(KeyboardButton(text="🎬 سناریو ریلز"))
    builder.add(KeyboardButton(text="📷 ایده بصری"))
    builder.add(KeyboardButton(text="📅 تقویم محتوایی"))
    builder.add(KeyboardButton(text="🔙 بازگشت"))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="نوع محتوا را انتخاب کنید..."
    )