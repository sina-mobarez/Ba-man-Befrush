from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
import re

from core.config import settings
from services.ai_service import AIService
from services.user_service import UserService
from keyboards.builders import (
    get_confirmation_payment_keyboard, get_start_keyboard, get_main_menu, get_content_type_keyboard, 
    get_profile_edit_keyboard, get_payment_keyboard, get_back_keyboard,
    get_confirmation_keyboard, get_discount_keyboard, get_onboarding_keyboard,
    get_profile_setup_keyboard
)
from models.schema import OnboardingStep, ContentType, SalesGoal, PageStyle, AudienceType

logger = logging.getLogger(__name__)

# States
class OnboardingStates(StatesGroup):
    waiting_for_ready = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_email = State()
    waiting_for_gallery_name = State()
    waiting_for_instagram = State()
    waiting_for_telegram = State()
    waiting_for_customers = State()
    waiting_for_constraints = State()
    waiting_for_help = State()
    waiting_for_physical_store = State()
    waiting_for_additional_info = State()
    waiting_for_summary_confirm = State()
    waiting_for_subscription_decision = State()
    viewing_scenarios = State()

class ContentGeneration(StatesGroup):
    waiting_for_content_type = State()
    waiting_for_caption_input = State()
    waiting_for_reels_input = State()
    waiting_for_visual_input = State()

class DiscountStates(StatesGroup):
    waiting_for_discount_code = State()

# Create router
router = Router()

# Help command
@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
🤖 راهنمای ربات تولید محتوا

🧠 تولید محتوا:
• کپشن نویسی: کپشن جذاب برای پست‌ها
• سناریو ریلز: ایده برای ویدیوهای کوتاه
• ایده بصری: پیشنهاد برای عکاسی محصولات

🎛️ ویرایش پروفایل:
• تغییر سبک، مخاطب و هدف
• اطلاعات کسب‌وکار

🔁 تمدید اشتراک:
• پرداخت ماهانه یا فصلی
• مشاهده وضعیت اشتراک

📞 پشتیبانی: @rez77
    """
    
    await message.answer(help_text.strip())

# Start command with referral support
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user_service: UserService):
    """Handle /start command with referral code support"""
    try:
        # Extract referral code from start parameter
        referral_code = None
        if message.text and len(message.text.split()) > 1:
            referral_code = message.text.split()[1]
        
        # Create or get user
        user = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            referred_by_code=referral_code
        )
        
        # Check if onboarding is completed
        if user.onboarding_completed:
            subscription = await user_service.get_user_subscription(user.id)
            is_subscribed = subscription.is_active if subscription else False
            
            welcome_back = f"""
سلام {user.display_name or user.first_name}! 👋

خوش برگشتی! آماده‌ام تا محتوای فوق‌العاده برای گالری‌ت تولید کنم.

{"🎯 اشتراک‌ت فعاله و می‌تونی از تمام امکانات استفاده کنی!" if is_subscribed else "⚠️ دوره آزمایشی‌ت تموم شده. برای ادامه، اشتراک تهیه کن."}
            """
            
            await message.answer(
                welcome_back.strip(),
                reply_markup=get_main_menu(is_subscribed)
            )
            await state.clear()
            return
        
        # Start onboarding flow
        welcome_text = """
سلام! من دستیار محتوای طلافروش هستم 💎

من سناریوهای ریلز اینستاگرامت رو کلمه به کلمه و تصویر به تصویر بهت میگم.

سناریوهایی که براساس شرایط تو و اصول محتوانویسی و با آنالیز محتوای وایرال نوشته شده.

برای شروع کار لازمه من یه سری اطلاعات از تو و گالری طلات داشته باشم تا در ادامه بتونم تقویم محتوایی و سناریو ریلزهات رو بهت بدم.

اگه آماده‌ای بزن روی "آماده‌ام":
        """
        
        if referral_code:
            welcome_text += f"\n\n🎁 با کد معرف وارد شدی! ممنون که به خانواده ما پیوستی."
        
        await message.answer(
            welcome_text.strip(),
            reply_markup=get_start_keyboard()
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.START)
        await state.set_state(OnboardingStates.waiting_for_ready)
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# Onboarding flow handlers
@router.message(F.text == "آماده‌ام", StateFilter(OnboardingStates.waiting_for_ready))
async def handle_ready(message: Message, state: FSMContext, user_service: UserService):
    """Handle ready confirmation"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        
        await message.answer(
            "عالی! 🎉\n\nچی صدات کنم؟",
            reply_markup=get_back_keyboard()
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.NAME)
        await state.set_state(OnboardingStates.waiting_for_name)
        
    except Exception as e:
        logger.error(f"Error in ready handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_name))
async def handle_name_input(message: Message, state: FSMContext, user_service: UserService):
    """Handle name input"""
    if message.text == "🔙 بازگشت":
        await back_to_start(message, state)
        return
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_user_display_name(user.id, message.text)
        
        await message.answer(
            f"خیلی خوشحالم {message.text} جان! 😊\n\n"
            "اگه مورد مهمی پیش اومد و میخواستم بهت پیام بدم، شمارت چنده؟",
            reply_markup=get_onboarding_keyboard("skip")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.PHONE)
        await state.set_state(OnboardingStates.waiting_for_phone)
        
    except Exception as e:
        logger.error(f"Error in name handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_phone))
async def handle_phone_input(message: Message, state: FSMContext, user_service: UserService):
    """Handle phone input"""
    if message.text == "رد کردن":
        phone = None
    elif message.text == "🔙 بازگشت":
        await back_to_name(message, state, user_service)
        return
    else:
        # Validate phone number
        phone_pattern = r'^(\+98|0)?9\d{9}$'
        if not re.match(phone_pattern, message.text):
            await message.answer(
                "شماره تلفن معتبر نیست. لطفاً شماره موبایل معتبر وارد کنید یا رد کنید:",
                reply_markup=get_onboarding_keyboard("skip")
            )
            return
        phone = message.text
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if phone:
            await user_service.update_user_phone(user.id, phone)
        
        await message.answer(
            "این مورد اختیاریه، اگه دوست داری مقاله‌های به‌روز برای تقویت طلافروشیت دریافت کنی، ایمیلت رو وارد کن:",
            reply_markup=get_onboarding_keyboard("skip")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.EMAIL)
        await state.set_state(OnboardingStates.waiting_for_email)
        
    except Exception as e:
        logger.error(f"Error in phone handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_email))
async def handle_email_input(message: Message, state: FSMContext, user_service: UserService):
    """Handle email input"""
    if message.text == "رد کردن":
        email = None
    elif message.text == "🔙 بازگشت":
        await back_to_phone(message, state, user_service)
        return
    else:
        # Validate email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, message.text):
            await message.answer(
                "ایمیل معتبر نیست. لطفاً ایمیل معتبر وارد کنید یا رد کنید:",
                reply_markup=get_onboarding_keyboard("skip")
            )
            return
        email = message.text
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if email:
            await user_service.update_user_email(user.id, email)
        
        await message.answer(
            "خب حالا بریم سراغ چندتا سوال در مورد کسب‌وکارت، تا بتونم سناریو منحصربه‌فرد تو رو بهت بدم.\n\n"
            "اول از همه، اسم گالریت چیه؟",
            reply_markup=get_back_keyboard()
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.GALLERY_NAME)
        await state.set_state(OnboardingStates.waiting_for_gallery_name)
        
    except Exception as e:
        logger.error(f"Error in email handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_gallery_name))
async def handle_gallery_name(message: Message, state: FSMContext, user_service: UserService):
    """Handle gallery name input"""
    if message.text == "🔙 بازگشت":
        await back_to_email(message, state, user_service)
        return
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_gallery_name(user.id, message.text)
        
        await message.answer(
            f"گالری {message.text} 👌\n\n"
            "آیدی پیج اینستاگرامت رو بده یه تحلیل بکنم:",
            reply_markup=get_back_keyboard()
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.INSTAGRAM)
        await state.set_state(OnboardingStates.waiting_for_instagram)
        
    except Exception as e:
        logger.error(f"Error in gallery name handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_instagram))
async def handle_instagram(message: Message, state: FSMContext, user_service: UserService):
    """Handle Instagram handle input"""
    if message.text == "🔙 بازگشت":
        await back_to_gallery_name(message, state, user_service)
        return
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        
        # Clean Instagram handle
        instagram = message.text.replace("@", "").replace("https://instagram.com/", "").strip()
        await user_service.update_instagram_handle(user.id, instagram)
        
        await message.answer(
            "اگر کانال تلگرام هم داری بفرست یه چک بکنم:",
            reply_markup=get_onboarding_keyboard("skip")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.TELEGRAM)
        await state.set_state(OnboardingStates.waiting_for_telegram)
        
    except Exception as e:
        logger.error(f"Error in Instagram handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_telegram))
async def handle_telegram_channel(message: Message, state: FSMContext, user_service: UserService):
    """Handle Telegram channel input"""
    if message.text == "رد کردن":
        telegram = None
    elif message.text == "🔙 بازگشت":
        await back_to_instagram(message, state, user_service)
        return
    else:
        telegram = message.text.replace("@", "").replace("https://t.me/", "").strip()
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if telegram:
            await user_service.update_telegram_channel(user.id, telegram)
        
        await message.answer(
            "بیشتر مشتریات کیا هستن؟\n\n"
            "مثلاً: خانم‌های جوان، آقایان میانسال، عروس‌خانم‌ها و...",
            reply_markup=get_back_keyboard()
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.CUSTOMERS)
        await state.set_state(OnboardingStates.waiting_for_customers)
        
    except Exception as e:
        logger.error(f"Error in Telegram handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_customers))
async def handle_customers(message: Message, state: FSMContext, user_service: UserService):
    """Handle main customers input"""
    if message.text == "🔙 بازگشت":
        await back_to_telegram(message, state, user_service)
        return
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_main_customers(user.id, message.text)
        
        await message.answer(
            "چه باید و نبایدهایی رو باید برای سناریو تو رعایت کنم؟\n\n"
            "مثل محدودیت‌های شخصی یا منابع خاص یا لحن منحصربه‌فرد",
            reply_markup=get_onboarding_keyboard("skip")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.CONSTRAINTS)
        await state.set_state(OnboardingStates.waiting_for_constraints)
        
    except Exception as e:
        logger.error(f"Error in customers handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_constraints))
async def handle_constraints(message: Message, state: FSMContext, user_service: UserService):
    """Handle constraints input"""
    if message.text == "رد کردن":
        constraints = None
    elif message.text == "🔙 بازگشت":
        await back_to_customers(message, state, user_service)
        return
    else:
        constraints = message.text
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if constraints:
            await user_service.update_constraints(user.id, constraints)
        
        await message.answer(
            "کسیو داری که توی تولید محتوا کمکت کنه؟\n\n"
            "مثال توی ضبط یا تدوین یا آپلود",
            reply_markup=get_onboarding_keyboard("skip")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.HELP)
        await state.set_state(OnboardingStates.waiting_for_help)
        
    except Exception as e:
        logger.error(f"Error in constraints handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_help))
async def handle_content_help(message: Message, state: FSMContext, user_service: UserService):
    """Handle content help input"""
    if message.text == "رد کردن":
        help_info = None
    elif message.text == "🔙 بازگشت":
        await back_to_constraints(message, state, user_service)
        return
    else:
        help_info = message.text
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if help_info:
            await user_service.update_content_help(user.id, help_info)
        
        await message.answer(
            "گالری حضوری هم داری یا نه هنوز؟",
            reply_markup=get_onboarding_keyboard("yes_no")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.PHYSICAL_STORE)
        await state.set_state(OnboardingStates.waiting_for_physical_store)
        
    except Exception as e:
        logger.error(f"Error in content help handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_physical_store))
async def handle_physical_store(message: Message, state: FSMContext, user_service: UserService):
    """Handle physical store question"""
    if message.text == "🔙 بازگشت":
        await back_to_help(message, state, user_service)
        return
    
    has_store = message.text in ["آره", "بله", "دارم"]
    
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_physical_store(user.id, has_store)
        
        await message.answer(
            "حله، من هر سوالی داشتم پرسیدم، اگه فکر میکنی چیز خاصی هست که من باید بدونم ولی نپرسیدم بگو، وگرنه ادامه بدیم:",
            reply_markup=get_onboarding_keyboard("continue")
        )
        
        await user_service.update_onboarding_step(user.id, OnboardingStep.ADDITIONAL_INFO)
        await state.set_state(OnboardingStates.waiting_for_additional_info)
        
    except Exception as e:
        logger.error(f"Error in content help handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(StateFilter(OnboardingStates.waiting_for_additional_info))
async def handle_additional_info(message: Message, state: FSMContext, user_service: UserService):
    """After additional info, show AI-generated summary and ask for confirmation"""
    if message.text == "🔙 بازگشت":
        await back_to_physical_store(message, state, user_service)
        return
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if message.text and message.text not in ["ادامه بدیم", "رد کردن"]:
            await user_service.update_additional_info(user.id, message.text)
        profile = await user_service.get_user_profile(user.id)
        ai = AIService()
        summary = await ai.generate_situation_summary(profile)
        await user_service.update_profile_summary_and_complete(user.id, summary, False)
        await message.answer(summary)
        await message.answer("آیا این خلاصه درست است؟", reply_markup=get_confirmation_keyboard())
        await user_service.update_onboarding_step(user.id, OnboardingStep.SUMMARY_CONFIRM)
        await state.set_state(OnboardingStates.waiting_for_summary_confirm)
    except Exception as e:
        logger.error(f"Error in additional info handler: {e}")
        await message.answer("خطایی رخ داده است.")

@router.callback_query(F.data.in_({"confirm_yes", "confirm_no"}))
async def handle_summary_confirmation(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    try:
        logger.info(f"Starting summary confirmation for user {callback.from_user.id}")
        logger.info(f"Callback data: {callback.data}")
        logger.info(f"State: {state}")
        logger.info(f"UserService type: {type(user_service)}")
        logger.info(f"UserService: {user_service}")
        logger.info("Getting user by telegram ID...")
        user = await user_service.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("کاربر یافت نشد.")
            return
            
        logger.info(f"User found: {user.id}")
        approved = callback.data == "confirm_yes"
        
        if approved:
            logger.info("User approved, getting profile...")
            # Get user profile and ensure it exists
            profile = await user_service.get_user_profile(user.id)
            if not profile:
                logger.info("Profile not found, creating one...")
                # Create profile if it doesn't exist
                await user_service.update_user_profile(user.id, gallery_name="گالری جدید")
                profile = await user_service.get_user_profile(user.id)
            
            # Save summary and complete onboarding
            await user_service.approved_profile_summary(user.id, approved)
            
            logger.info("Generating AI scenarios...")
            # Generate 3 reels scenarios using AI
            ai_service = AIService()
            try:
                scenarios = await ai_service.generate_reels_scenario(
                    theme="معرفی گالری طلا و جواهرات",
                    user_profile=profile
                )
                logger.info("AI scenarios generated successfully")
            except Exception as e:
                logger.error(f"Error generating scenarios: {e}")
                scenarios = [
                    "سناریو 1: معرفی گالری با نمایش محصولات",
                    "سناریو 2: آموزش انتخاب طلا",
                    "سناریو 3: نمایش کارهای سفارشی"
                ]
            
            logger.info("Saving scenarios to history...")
            # Save scenarios to history
            scenarios_text = "\n\n---\n\n".join(scenarios)
            await user_service.save_content_history(
                user.id,
                ContentType.REELS,
                "onboarding_scenarios",
                scenarios_text
            )
            
            logger.info("Showing first scenario to user...")
            # Store scenarios in state data for step-by-step viewing
            await state.update_data(
                scenarios=scenarios,
                current_scenario=1,
                total_scenarios=len(scenarios)
            )
            
            # Show first scenario with navigation
            first_scenario = format_scenario_message(scenarios[0], 1, len(scenarios))
            
            await callback.message.edit_text(
                first_scenario,
                reply_markup=get_scenario_navigation_keyboard(1, len(scenarios))
            )
            
            await state.set_state(OnboardingStates.viewing_scenarios)
            logger.info("Summary confirmation completed successfully")
            
        else:
            await callback.message.edit_text("باشه، هرجایی نیاز بود اصلاح کن و دوباره ادامه بده.")
            await state.clear()
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in summary confirmation: {e}")
        await callback.answer("خطایی رخ داده است.")

# Scenario navigation handlers
@router.callback_query(F.data.startswith("scenario_"))
async def handle_scenario_navigation(callback: CallbackQuery, state: FSMContext):
    """Handle scenario navigation (prev/next/continue)"""
    try:
        data = await state.get_data()
        scenarios = data.get('scenarios', [])
        current = data.get('current_scenario', 1)
        total = data.get('total_scenarios', len(scenarios))
        
        if not scenarios:
            await callback.answer("خطا در دریافت سناریوها.")
            return
        
        if callback.data.startswith("scenario_prev_"):
            # Previous scenario
            new_current = max(1, current - 1)
            await state.update_data(current_scenario=new_current)
            
            scenario_text = format_scenario_message(scenarios[new_current - 1], new_current, total)
            await callback.message.edit_text(
                scenario_text,
                reply_markup=get_scenario_navigation_keyboard(new_current, total)
            )
            
        elif callback.data.startswith("scenario_next_"):
            # Next scenario
            new_current = min(total, current + 1)
            await state.update_data(current_scenario=new_current)
            
            scenario_text = format_scenario_message(scenarios[new_current - 1], new_current, total)
            await callback.message.edit_text(
                scenario_text,
                reply_markup=get_scenario_navigation_keyboard(new_current, total)
            )
            
        elif callback.data == "scenario_continue":
            # Continue to subscription decision
            subscription_question = (
                "خب، حالا که نحوه کارم رو دیدی... 🤓\n"
                "اگر حس کردی اینجور آدمی می‌تونه به گالریت کمک کنه، می‌تونیم با هم همکار بشیم!\n\n"
                "هر ماه فقط ۹۸۰ هزار تومان (به قیمت یه دستبند ساده!) و من:\n"
                "✅ تقویم محتوایی آماده می‌دم\n"
                "✅ ریلزهای حرفه‌ای طراحی می‌کنم\n"
                "✅ کلی ایده نو برای فروش بیشتر می‌ریزم تو جیبت!\n\n"
                "پس... میخوای استخدامم کنی؟ 😎"
            )
            
            await callback.message.edit_text(
                subscription_question,
                reply_markup=get_confirmation_payment_keyboard()
            )
            
            await state.set_state(OnboardingStates.waiting_for_subscription_decision)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in scenario navigation: {e}")
        await callback.answer("خطایی رخ داده است.")

@router.callback_query(F.data.in_({"now", "later"}), StateFilter(OnboardingStates.waiting_for_subscription_decision))
async def handle_subscription_decision(callback: CallbackQuery, state: FSMContext):
    try:
        wants_subscription = callback.data == "now"
        
        if wants_subscription:
            await callback.message.edit_text("عالی! برای ادامه یکی از گزینه‌های پرداخت را انتخاب کنید:")
            await callback.message.answer("گزینه پرداخت:", reply_markup=get_payment_keyboard())
        else:
            await callback.message.edit_text("باشه، هر وقت خواستی می‌تونی از منوی اصلی اشتراک تهیه کنی.")
            await callback.message.answer("بازگشت به منوی اصلی", reply_markup=get_main_menu(False))
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in subscription decision: {e}")
        await callback.answer("خطایی رخ داده است.")

@router.callback_query(F.data.startswith("goal_"))
async def handle_goal_selection(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    """Handle goal selection"""
    try:
        parts = callback.data.split("_")
        goal_name = "_".join(parts[1:]).upper() 
        goal = SalesGoal[goal_name]
        
        data = await state.get_data()
        data['sales_goal'] = goal
        
        # Save profile
        user = await user_service.get_or_create_user(telegram_id=callback.from_user.id)
        
        success = await user_service.update_user_profile(
            user.id,
            page_style=data['page_style'],
            audience_type=data['audience_type'],
            sales_goal=data['sales_goal']
        )
        
        if success:
            subscription = await user_service.get_user_subscription(user.id)
            is_subscribed = subscription.is_active if subscription else False
            
            success_text = f"""
تبریک! پروفایل شما تکمیل شد ✅

🎨 سبک: {data['page_style'].value}
👥 مخاطب: {data['audience_type'].value}  
🎯 هدف: {goal.value}

حالا می‌تونی شروع کنی و محتوای فوق‌العاده تولید کنی! 🚀

{f"🎁 شما {settings.TRIAL_DAYS} روز آزمایشی دارید." if is_subscribed else ""}
            """
            
            await callback.message.edit_text(success_text.strip())
            await callback.message.answer(
                "چه کاری می‌تونم برای شما انجام بدهم؟",
                reply_markup=get_main_menu(is_subscribed)
            )
            await state.clear()
        else:
            await callback.message.edit_text("خطا در ذخیره پروفایل. لطفاً دوباره تلاش کنید.")
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in goal selection: {e}")
        await callback.answer("خطایی رخ داده است.")

# Main menu handlers
@router.message(F.text == "🧠 تولید محتوا")
async def handle_content_generation(message: Message, state: FSMContext, user_service: UserService):
    """Handle content generation menu"""
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        
        # Check subscription
        subscription = await user_service.get_user_subscription(user.id)
        if not subscription or not subscription.is_active:
            await message.answer(
                "برای استفاده از تولید محتوا، ابتدا باید اشتراک داشته باشید.",
                reply_markup=get_payment_keyboard()
            )
            return
        
        await message.answer(
            "چه نوع محتوایی می‌خواید تولید کنید؟",
            reply_markup=get_content_type_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_content_type)
        
    except Exception as e:
        logger.error(f"Error in content generation: {e}")
        await message.answer("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

@router.message(F.text == "📅 تقویم محتوایی", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_calendar_request(message: Message, state: FSMContext, user_service: UserService):
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        profile = await user_service.get_user_profile(user.id)
        if not profile:
            await message.answer("لطفاً ابتدا پروفایل خود را تکمیل کنید. /profile")
            return
        loading_msg = await message.answer("در حال تولید تقویم محتوایی... 📅")
        ai = AIService()
        ideas = await ai.generate_content_calendar(profile)
        await user_service.save_content_history(user.id, ContentType.CALENDAR, "content_calendar", "\n\n---\n\n".join(ideas))
        await loading_msg.delete()
        result_text = "📅 تقویم محتوایی پیشنهادی:\n\n" + "\n\n---\n\n".join(ideas)
        await message.answer(result_text)
        await state.set_state(ContentGeneration.waiting_for_content_type)
    except Exception as e:
        logger.error(f"Error generating calendar: {e}")
        await message.answer("خطا در تولید تقویم محتوایی. دوباره تلاش کنید.")

@router.message(F.text == "✍️ کپشن نویسی", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_caption_request(message: Message, state: FSMContext):
    """Handle caption generation request"""
    await message.answer(
        "محصول یا موضوعی که می‌خواید کپشن براش بنویسم رو توضیح بدید:\n\n"
        "مثال: انگشتر طلا با نگین الماس برای عروس‌خانم‌ها",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(ContentGeneration.waiting_for_caption_input)

@router.message(F.text == "🎬 سناریو ریلز", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_reels_request(message: Message, state: FSMContext):
    """Handle reels scenario request"""
    await message.answer(
        "موضوع یا مناسبتی که می‌خواید سناریو ریلز براش داشته باشید رو بگید:\n\n"
        "مثال: فروش ویژه شب یلدا، معرفی مجموعه جدید، ولنتاین",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(ContentGeneration.waiting_for_reels_input)

@router.message(F.text == "📷 ایده بصری", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_visual_request(message: Message, state: FSMContext):
    """Handle visual ideas request"""
    await message.answer(
        "نوع محصولی که می‌خواید ایده عکاسی براش داشته باشید رو بگید:\n\n"
        "مثال: دستبند طلا، گردنبند مروارید، حلقه نامزدی\n"
        "اگر وسایل خاصی در دسترس دارید هم بگید.",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(ContentGeneration.waiting_for_visual_input)

# Content generation handlers
@router.message(StateFilter(ContentGeneration.waiting_for_caption_input))
async def generate_captions(message: Message, state: FSMContext, user_service: UserService):
    """Generate captions for user input"""
    if message.text == "🔙 بازگشت":
        await back_to_main_menu(message, state)
        return
    
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        profile = await user_service.get_user_profile(user.id)
        
        if not profile:
            await message.answer("لطفاً ابتدا پروفایل خود را تکمیل کنید. /profile")
            return
        
        # Show loading message
        loading_msg = await message.answer("در حال تولید کپشن... ⏳")
        
        # Generate captions
        ai_service = AIService()
        captions = await ai_service.generate_caption(
            product_description=message.text,
            user_profile=profile
        )
        
        # Save to history
        captions_text = "\n\n---\n\n".join(captions)
        await user_service.save_content_history(
            user.id,
            ContentType.CAPTION,
            message.text,
            captions_text
        )
        
        # Send results
        await loading_msg.delete()
        
        result_text = "🎯 کپشن‌های پیشنهادی:\n\n"
        for i, caption in enumerate(captions, 1):
            result_text += f"کپشن {i}:\n{caption}\n\n---\n\n"
        
        await message.answer(result_text.strip())
        await message.answer(
            "کپشن‌ها آماده شد! ✅\nمی‌خواید محتوای دیگری تولید کنید؟",
            reply_markup=get_content_type_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_content_type)
        
    except Exception as e:
        logger.error(f"Error generating captions: {e}")
        await message.answer("خطا در تولید کپشن. لطفاً دوباره تلاش کنید.")

@router.message(StateFilter(ContentGeneration.waiting_for_reels_input))
async def generate_reels_scenarios(message: Message, state: FSMContext, user_service: UserService):
    """Generate reels scenarios"""
    if message.text == "🔙 بازگشت":
        await back_to_main_menu(message, state)
        return
    
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        profile = await user_service.get_user_profile(user.id)
        
        if not profile:
            await message.answer("لطفاً ابتدا پروفایل خود را تکمیل کنید. /profile")
            return
        
        loading_msg = await message.answer("در حال تولید سناریو ریلز... 🎬")
        
        ai_service = AIService()
        scenarios = await ai_service.generate_reels_scenario(
            theme=message.text,
            user_profile=profile
        )
        
        # Save to history
        scenarios_text = "\n\n---\n\n".join(scenarios)
        await user_service.save_content_history(
            user.id,
            ContentType.REELS,
            message.text,
            scenarios_text
        )
        
        await loading_msg.delete()
        
        result_text = "🎬 سناریوهای ریلز پیشنهادی:\n\n"
        for i, scenario in enumerate(scenarios, 1):
            result_text += f"\n{scenario}\n\n---\n\n"
        
        await message.answer(result_text.strip())
        await message.answer(
            "سناریوها آماده شد! ✅\nمی‌خواید محتوای دیگری تولید کنید؟",
            reply_markup=get_content_type_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_content_type)
        
    except Exception as e:
        logger.error(f"Error generating reels: {e}")
        await message.answer("خطا در تولید سناریو ریلز. لطفاً دوباره تلاش کنید.")

@router.message(StateFilter(ContentGeneration.waiting_for_visual_input))
async def generate_visual_ideas(message: Message, state: FSMContext, user_service: UserService):
    """Generate visual ideas"""
    if message.text == "🔙 بازگشت":
        await back_to_main_menu(message, state)
        return
    
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        profile = await user_service.get_user_profile(user.id)
        
        if not profile:
            await message.answer("لطفاً ابتدا پروفایل خود را تکمیل کنید. /profile")
            return
        
        loading_msg = await message.answer("در حال تولید ایده‌های بصری... 📷")
        
        ai_service = AIService()
        ideas = await ai_service.generate_visual_ideas(
            product_type=message.text,
            user_profile=profile
        )
        
        # Save to history
        ideas_text = "\n\n---\n\n".join(ideas)
        await user_service.save_content_history(
            user.id,
            ContentType.VISUAL,
            message.text,
            ideas_text
        )
        
        await loading_msg.delete()
        
        result_text = "📷 ایده‌های بصری پیشنهادی:\n\n"
        result_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, idea in enumerate(ideas, 1):
            formatted_idea = format_visual_idea_message(idea)
            result_text += f"{formatted_idea}\n\n"
            if i < len(ideas):
                result_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        await message.answer(result_text.strip())
        await message.answer(
            "ایده‌ها آماده شد! ✅\nمی‌خواید محتوای دیگری تولید کنید؟",
            reply_markup=get_content_type_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_content_type)
        
    except Exception as e:
        logger.error(f"Error generating visual ideas: {e}")
        await message.answer("خطا در تولید ایده بصری. لطفاً دوباره تلاش کنید.")

# Subscription handlers
@router.message(F.text == "🔁 تمدید اشتراک")
async def handle_subscription_renewal(message: Message, user_service: UserService):
    """Handle subscription renewal"""
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        subscription = await user_service.get_user_subscription(user.id)
        
        if subscription and subscription.is_active:
            expiry_date = subscription.expires_at.strftime('%Y/%m/%d')
            await message.answer(
                f"اشتراک شما تا {expiry_date} فعال است.\n"
                f"برای تمدید زودهنگام، گزینه موردنظر را انتخاب کنید:",
                reply_markup=get_payment_keyboard()
            )
        else:
            await message.answer(
                "اشتراک شما منقضی شده است.\n"
                "برای ادامه استفاده از خدمات، یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=get_payment_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error in subscription renewal: {e}")
        await message.answer("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

@router.message(F.text == "🎁 کد تخفیف")
async def handle_discount_entry(message: Message, state: FSMContext):
    await message.answer("کد تخفیف را ارسال کنید:", reply_markup=get_discount_keyboard())
    await state.set_state(DiscountStates.waiting_for_discount_code)

@router.message(StateFilter(DiscountStates.waiting_for_discount_code))
async def handle_discount_code(message: Message, state: FSMContext, user_service: UserService):
    if message.text == "🔙 بازگشت":
        await back_to_main_menu(message, state)
        return
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        discount = await user_service.apply_discount_code(message.text.strip(), user.id)
        if not discount:
            await message.answer("کد تخفیف معتبر نیست یا منقضی شده است.")
            return
        await user_service.update_subscription_discount(user.id, discount)
        await message.answer(f"کد تخفیف با موفقیت اعمال شد: {int(discount.discount_percentage*100)}%")
        await back_to_main_menu(message, state, user_service)
    except Exception as e:
        logger.error(f"Error applying discount code: {e}")
        await message.answer("خطا در اعمال کد تخفیف.")

@router.callback_query(F.data.startswith("payment_"))
async def handle_payment_selection(callback: CallbackQuery):
    """Handle payment option selection"""
    try:
        # Parse payment data
        parts = callback.data.split("_")
        payment_type = parts[1]  # monthly or seasonal
        amount = int(parts[2])
        
        # Generate payment link (mock implementation)
        payment_link = f"https://zarinpal.com/pg/StartPay/mock-{callback.from_user.id}-{amount}"
        
        payment_text = f"""
💳 پرداخت {payment_type}

مبلغ: {amount:,} تومان
لینک پرداخت: {payment_link}

⚠️ پس از پرداخت، لطفاً کد پیگیری را برای ما ارسال کنید تا اشتراک‌تان فعال شود.
        """
        
        await callback.message.edit_text(payment_text.strip())
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in payment selection: {e}")
        await callback.answer("خطایی رخ داده است.")

# Utility handlers
@router.message(F.text == "🔙 بازگشت")
async def back_to_main_menu(message: Message, state: FSMContext, user_service: UserService | None = None):
    """Return to main menu"""
    try:
        is_subscribed = False
        if user_service is not None:
            user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
            subscription = await user_service.get_user_subscription(user.id)
            is_subscribed = subscription.is_active if subscription else False
        
        await message.answer(
            "بازگشت به منوی اصلی",
            reply_markup=get_main_menu(is_subscribed)
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error returning to main menu: {e}")
        await message.answer("خطایی رخ داده است.")

@router.message(F.text == "❓ راهنما")
async def handle_help(message: Message):
    """Handle help command"""
    help_text = """
🤖 راهنمای ربات تولید محتوا

🧠 تولید محتوا:
• کپشن نویسی: کپشن جذاب برای پست‌ها
• سناریو ریلز: ایده برای ویدیوهای کوتاه
• ایده بصری: پیشنهاد برای عکاسی محصولات

🎛️ ویرایش پروفایل:
• تغییر سبک، مخاطب و هدف
• اطلاعات کسب‌وکار

🔁 تمدید اشتراک:
• پرداخت ماهانه یا فصلی
• مشاهده وضعیت اشتراک

📞 پشتیبانی: @rez77
    """
    
    await message.answer(help_text.strip())

@router.message()
async def handle_unknown_message(message: Message):
    """Handle unknown messages"""
    await message.answer(
        "متوجه نشدم چی گفتید. 🤔\n"
        "از منو یکی از گزینه‌ها رو انتخاب کنید یا /help بزنید."
    )

def format_scenario_message(scenario: str, scenario_num: int, total: int) -> str:
    """Format scenario as professional Telegram message"""
    formatted = f"🎬 سناریو {scenario_num} از {total}\n\n"
    formatted += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Clean and format the scenario content
    lines = scenario.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line:
            # Add proper formatting for different sections
            if line.startswith('📋') or line.startswith('🎬') or line.startswith('✍️') or line.startswith('🎵') or line.startswith('⏱️') or line.startswith('🎯'):
                formatted += f"\n{line}\n"
            elif line.startswith('سناریو'):
                formatted += f"**{line}**\n"
            else:
                formatted += f"{line}\n"
    
    formatted += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return formatted

def format_visual_idea_message(idea: str) -> str:
    """Format visual idea as professional Telegram message"""
    formatted = ""
    
    # Clean and format the idea content
    lines = idea.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line:
            # Add proper formatting for different sections
            if line.startswith('📸') or line.startswith('📐') or line.startswith('💡') or line.startswith('🎨') or line.startswith('🖼️') or line.startswith('💎'):
                formatted += f"{line}\n"
            elif line.startswith('ایده'):
                formatted += f"**{line}**\n\n"
            else:
                formatted += f"{line}\n"
    
    return formatted.strip()

def get_scenario_navigation_keyboard(current: int, total: int):
    """Create navigation keyboard for scenarios"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    keyboard = InlineKeyboardBuilder()
    
    # Navigation buttons
    if current > 1:
        keyboard.add(InlineKeyboardButton(
            text="⬅️ قبلی", 
            callback_data=f"scenario_prev_{current}"
        ))
    
    if current < total:
        keyboard.add(InlineKeyboardButton(
            text="بعدی ➡️", 
            callback_data=f"scenario_next_{current}"
        ))
    
    # Always show continue button
    keyboard.add(InlineKeyboardButton(
        text="ادامه فرآیند", 
        callback_data="scenario_continue"
    ))
    
    keyboard.adjust(2, 1)
    return keyboard.as_markup()

def register_handlers() -> Router:
    """Register all handlers and return router"""
    return router

# =============================
# Back navigation helper functions
# =============================

async def back_to_start(message: Message, state: FSMContext):
    """Go back to start readiness confirmation"""
    await message.answer(
        "برگردیم به شروع. اگر آماده‌ای بزن روی \"آماده‌ام\":",
        reply_markup=get_start_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_ready)

async def back_to_name(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking user's display name"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.NAME)
    except Exception:
        pass
    await message.answer(
        "چی صدات کنم؟",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_name)

async def back_to_phone(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking for phone number"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.PHONE)
    except Exception:
        pass
    await message.answer(
        "شماره موبایل‌ت رو وارد کن یا رد کن:",
        reply_markup=get_onboarding_keyboard("skip")
    )
    await state.set_state(OnboardingStates.waiting_for_phone)

async def back_to_email(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking for email"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.EMAIL)
    except Exception:
        pass
    await message.answer(
        "ایمیلت رو وارد کن یا رد کن:",
        reply_markup=get_onboarding_keyboard("skip")
    )
    await state.set_state(OnboardingStates.waiting_for_email)

async def back_to_gallery_name(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking for gallery name"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.GALLERY_NAME)
    except Exception:
        pass
    await message.answer(
        "اسم گالریت چیه؟",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_gallery_name)

async def back_to_instagram(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking for Instagram handle"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.INSTAGRAM)
    except Exception:
        pass
    await message.answer(
        "آیدی پیج اینستاگرامت رو بده:",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_instagram)

async def back_to_telegram(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking for Telegram channel"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.TELEGRAM)
    except Exception:
        pass
    await message.answer(
        "اگر کانال تلگرام هم داری بفرست، یا رد کن:",
        reply_markup=get_onboarding_keyboard("skip")
    )
    await state.set_state(OnboardingStates.waiting_for_telegram)

async def back_to_customers(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking about main customers"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.CUSTOMERS)
    except Exception:
        pass
    await message.answer(
        "بیشتر مشتریات کیا هستن؟",
        reply_markup=get_back_keyboard()
    )
    await state.set_state(OnboardingStates.waiting_for_customers)

async def back_to_constraints(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking about constraints"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.CONSTRAINTS)
    except Exception:
        pass
    await message.answer(
        "چه باید و نبایدهایی رو باید رعایت کنم؟ می‌تونی رد کنی:",
        reply_markup=get_onboarding_keyboard("skip")
    )
    await state.set_state(OnboardingStates.waiting_for_constraints)

async def back_to_help(message: Message, state: FSMContext, user_service: UserService):
    """Go back to asking about content help"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.HELP)
    except Exception:
        pass
    await message.answer(
        "کسی هست توی تولید محتوا کمکت کنه؟ می‌تونی رد کنی:",
        reply_markup=get_onboarding_keyboard("skip")
    )
    await state.set_state(OnboardingStates.waiting_for_help)

async def back_to_physical_store(message: Message, state: FSMContext, user_service: UserService):
    """Go back to physical store question"""
    try:
        user = await user_service.get_user_by_telegram_id(message.from_user.id)
        await user_service.update_onboarding_step(user.id, OnboardingStep.PHYSICAL_STORE)
    except Exception:
        pass
    await message.answer(
        "گالری حضوری هم داری یا نه هنوز؟",
        reply_markup=get_onboarding_keyboard("yes_no")
    )
    await state.set_state(OnboardingStates.waiting_for_physical_store)