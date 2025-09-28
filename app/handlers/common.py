from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, Voice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

from core.config import settings
from services.ai_service import AIService
from services.user_service import UserService
from services.speech_service import SpeechService
from keyboards.builders import (
    get_main_menu, get_content_type_keyboard, get_profile_setup_keyboard,
    get_profile_edit_keyboard, get_payment_keyboard, get_back_keyboard
)
from models.schema import PageStyle, AudienceType, SalesGoal, ContentType

logger = logging.getLogger(__name__)

# States
class ProfileSetup(StatesGroup):
    waiting_for_style = State()
    waiting_for_audience = State()
    waiting_for_goal = State()
    waiting_for_business_name = State()

class ContentGeneration(StatesGroup):
    waiting_for_content_type = State()
    waiting_for_caption_input = State()
    waiting_for_reels_input = State()
    waiting_for_visual_input = State()
    waiting_for_voice_confirmation = State()

class ProfileEdit(StatesGroup):
    editing_style = State()
    editing_audience = State()
    editing_goal = State()
    editing_business = State()

# Create router
router = Router()

# Command handlers
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user_service: UserService):
    """Handle /start command"""
    try:
        # Create or get user
        user = await user_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Check if profile is complete
        profile = await user_service.get_user_profile(user.id)
        
        if not profile or not profile.page_style:
            welcome_text = """
سلام! من دستیار هوش مصنوعی تولید محتوای شما هستم 💎

برای شروع، لطفاً پروفایل خودتان را تکمیل کنید تا بتوانم محتوای مناسب‌تری برایتان تولید کنم.

اول بگید که سبک پیج‌تون چیه؟
            """
            await message.answer(
                welcome_text.strip(),
                reply_markup=get_profile_setup_keyboard("style")
            )
            await state.set_state(ProfileSetup.waiting_for_style)
        else:
            subscription = await user_service.get_user_subscription(user.id)
            is_subscribed = subscription.is_active if subscription else False
            
            if is_subscribed:
                welcome_back = f"""
خوش برگشتید! 🎉

آماده تولید محتوای فوق‌العاده برای کسب‌وکارتان هستم.
اشتراک شما تا {subscription.expires_at.strftime('%Y/%m/%d')} فعال است.

چه کاری می‌تونم برای شما انجام بدهم؟
                """
            else:
                welcome_back = """
خوش برگشتید! 

دوره آزمایشی شما به پایان رسیده است. برای ادامه استفاده از خدمات، لطفاً اشتراک خود را تمدید کنید.
                """
            
            await message.answer(
                welcome_back.strip(),
                reply_markup=get_main_menu(is_subscribed)
            )
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

@router.message(Command("profile"))
async def cmd_profile(message: Message, user_service: UserService):
    """Handle /profile command"""
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)
        profile = await user_service.get_user_profile(user.id)
        
        if not profile:
            await message.answer("پروفایل شما یافت نشد. لطفاً دوباره /start کنید.")
            return
        
        profile_text = f"""
📊 پروفایل شما:

🎨 سبک پیج: {profile.page_style.value if profile.page_style else 'تنظیم نشده'}
👥 نوع مخاطب: {profile.audience_type.value if profile.audience_type else 'تنظیم نشده'}
🎯 هدف فروش: {profile.sales_goal.value if profile.sales_goal else 'تنظیم نشده'}

{f"🏪 نام کسب‌وکار: {profile.business_name}" if profile.business_name else ""}
{f"📝 توضیحات: {profile.business_description}" if profile.business_description else ""}
{f"📱 اینستاگرام: @{profile.instagram_handle}" if profile.instagram_handle else ""}
        """
        
        await message.answer(
            profile_text.strip(),
            reply_markup=get_profile_edit_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
        await message.answer("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# Profile setup handlers
@router.callback_query(F.data.startswith("style_"))
async def handle_style_selection(callback: CallbackQuery, state: FSMContext):
    """Handle style selection"""
    try:
        parts = callback.data.split("_")
        style_name = "_".join(parts[1:]).upper() 
        style = PageStyle[style_name]
        
        await state.update_data(page_style=style)
        
        await callback.message.edit_text(
            f"عالی! سبک «{style.value}» انتخاب شد.\n\nحالا بگید مخاطب اصلی‌تون کیان؟",
            reply_markup=get_profile_setup_keyboard("audience")
        )
        await state.set_state(ProfileSetup.waiting_for_audience)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in style selection: {e}")
        await callback.answer("خطایی رخ داده است.")

@router.callback_query(F.data.startswith("audience_"))
async def handle_audience_selection(callback: CallbackQuery, state: FSMContext):
    """Handle audience selection"""
    try:
        parts = callback.data.split("_")
        audience_name = "_".join(parts[1:]).upper() 
        audience = AudienceType[audience_name]
        
        await state.update_data(audience_type=audience)
        
        await callback.message.edit_text(
            f"مخاطب «{audience.value}» انتخاب شد.\n\nهدف اصلی‌تون از تولید محتوا چیه؟",
            reply_markup=get_profile_setup_keyboard("goal")
        )
        await state.set_state(ProfileSetup.waiting_for_goal)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in audience selection: {e}")
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

حالا می‌تونید شروع کنید و محتوای فوق‌العاده تولید کنید! 🚀

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

@router.message(F.text == "✍️ کپشن نویسی", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_caption_request(message: Message, state: FSMContext, user_service: UserService):
    """Handle caption generation request"""
    data = await state.get_data()
    voice_input = data.get('user_input')

    if voice_input:
        # User came from voice input, use it directly for caption generation
        await message.answer(f"در حال تولید کپشن برای: \"{voice_input}\" ⏳")

        # Simulate a message with the voice input for the caption generator
        class VoiceInputMessage:
            def __init__(self, text, from_user):
                self.text = text
                self.from_user = from_user

        voice_message = VoiceInputMessage(voice_input, message.from_user)
        await generate_captions(voice_message, state, user_service)
    else:
        # Normal text input flow
        await message.answer(
            "محصول یا موضوعی که می‌خواید کپشن براش بنویسم رو توضیح بدید:\n\n"
            "مثال: انگشتر طلا با نگین الماس برای عروس‌خانم‌ها\n\n"
            "💡 نکته: می‌توانید به جای تایپ، پیام صوتی ارسال کنید!",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_caption_input)

@router.message(F.text == "🎬 سناریو ریلز", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_reels_request(message: Message, state: FSMContext, user_service: UserService):
    """Handle reels scenario request"""
    data = await state.get_data()
    voice_input = data.get('user_input')

    if voice_input:
        # User came from voice input, use it directly for reels generation
        await message.answer(f"در حال تولید سناریو ریلز برای: \"{voice_input}\" 🎬")

        # Simulate a message with the voice input for the reels generator
        class VoiceInputMessage:
            def __init__(self, text, from_user):
                self.text = text
                self.from_user = from_user

        voice_message = VoiceInputMessage(voice_input, message.from_user)
        await generate_reels_scenarios(voice_message, state, user_service)
    else:
        # Normal text input flow
        await message.answer(
            "موضوع یا مناسبتی که می‌خواید سناریو ریلز براش داشته باشید رو بگید:\n\n"
            "مثال: فروش ویژه شب یلدا، معرفی مجموعه جدید، ولنتاین\n\n"
            "💡 نکته: می‌توانید به جای تایپ، پیام صوتی ارسال کنید!",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_reels_input)

@router.message(F.text == "📷 ایده بصری", StateFilter(ContentGeneration.waiting_for_content_type))
async def handle_visual_request(message: Message, state: FSMContext, user_service: UserService):
    """Handle visual ideas request"""
    data = await state.get_data()
    voice_input = data.get('user_input')

    if voice_input:
        # User came from voice input, use it directly for visual ideas generation
        await message.answer(f"در حال تولید ایده‌های بصری برای: \"{voice_input}\" 📷")

        # Simulate a message with the voice input for the visual ideas generator
        class VoiceInputMessage:
            def __init__(self, text, from_user):
                self.text = text
                self.from_user = from_user

        voice_message = VoiceInputMessage(voice_input, message.from_user)
        await generate_visual_ideas(voice_message, state, user_service)
    else:
        # Normal text input flow
        await message.answer(
            "نوع محصولی که می‌خواید ایده عکاسی براش داشته باشید رو بگید:\n\n"
            "مثال: دستبند طلا، گردنبند مروارید، حلقه نامزدی\n"
            "اگر وسایل خاصی در دسترس دارید هم بگید.\n\n"
            "💡 نکته: می‌توانید به جای تایپ، پیام صوتی ارسال کنید!",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(ContentGeneration.waiting_for_visual_input)

# Content generation handlers
# Voice support for content input states
@router.message(F.voice, StateFilter(ContentGeneration.waiting_for_caption_input))
async def handle_voice_caption_input(message: Message, state: FSMContext, user_service: UserService):
    """Handle voice input for caption generation"""
    try:
        # Show processing message
        processing_msg = await message.answer("🎤 در حال تبدیل صدا به متن...")

        # Initialize speech service
        speech_service = SpeechService()

        # Process voice message
        transcribed_text = await speech_service.process_voice_message(
            message.bot,
            message.voice.file_id,
            voice_duration=message.voice.duration,
            voice_file_size=message.voice.file_size
        )

        if not transcribed_text.strip():
            await processing_msg.edit_text("❌ متأسفانه نتوانستم صدای شما را تشخیص دهم. لطفاً دوباره تلاش کنید.")
            return

        await processing_msg.delete()

        # Use transcribed text for caption generation
        class VoiceInputMessage:
            def __init__(self, text, from_user):
                self.text = text
                self.from_user = from_user

        voice_message = VoiceInputMessage(transcribed_text, message.from_user)
        await generate_captions(voice_message, state, user_service, from_voice=True)

    except ValueError as ve:
        # Handle validation errors (file too large, too long, etc.)
        await processing_msg.edit_text(f"❌ {str(ve)}")
    except Exception as e:
        logger.error(f"Error processing voice caption input: {e}")
        await message.answer("خطا در تبدیل صدا به متن. لطفاً از متن استفاده کنید.")

@router.message(StateFilter(ContentGeneration.waiting_for_caption_input))
async def generate_captions(message: Message, state: FSMContext, user_service: UserService, from_voice: bool = False):
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
            user_profile=profile,
            from_voice=from_voice
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
            result_text += f"سناریو {i}:\n{scenario}\n\n---\n\n"
        
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
        for i, idea in enumerate(ideas, 1):
            result_text += f"ایده {i}:\n{idea}\n\n---\n\n"
        
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

# Voice message handlers
@router.message(F.voice)
async def handle_voice_message(message: Message, state: FSMContext, user_service: UserService):
    """Handle voice message for speech-to-text conversion"""
    try:
        user = await user_service.get_or_create_user(telegram_id=message.from_user.id)

        # Check subscription
        subscription = await user_service.get_user_subscription(user.id)
        if not subscription or not subscription.is_active:
            await message.answer(
                "برای استفاده از قابلیت تبدیل صدا به متن، ابتدا باید اشتراک داشته باشید.",
                reply_markup=get_payment_keyboard()
            )
            return

        # Show processing message
        processing_msg = await message.answer("🎤 در حال تبدیل صدا به متن...\nلطفاً کمی صبر کنید.")

        try:
            # Initialize speech service
            speech_service = SpeechService()

            # Process voice message
            transcribed_text = await speech_service.process_voice_message(
                message.bot,
                message.voice.file_id,
                voice_duration=message.voice.duration,
                voice_file_size=message.voice.file_size
            )

            if not transcribed_text.strip():
                await processing_msg.edit_text("❌ متأسفانه نتوانستم صدای شما را تشخیص دهم. لطفاً دوباره تلاش کنید.")
                return

        except ValueError as ve:
            # Handle validation errors (file too large, too long, etc.)
            await processing_msg.edit_text(f"❌ {str(ve)}")
            return

        # Delete processing message
        await processing_msg.delete()

        # Show transcription to user for confirmation
        confirmation_text = f"""
🎯 متن تشخیص داده شده:

"{transcribed_text}"

✅ اگر متن درست است، روی "تولید محتوا" کلیک کنید
✏️ اگر می‌خواهید متن را ویرایش کنید، آن را دوباره تایپ کنید
🔙 یا می‌توانید بازگشت کنید
        """

        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ تولید محتوا", callback_data="confirm_voice_text")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="cancel_voice")]
        ])

        await message.answer(confirmation_text.strip(), reply_markup=keyboard)

        # Store transcribed text in state
        await state.update_data(voice_transcript=transcribed_text)
        await state.set_state(ContentGeneration.waiting_for_voice_confirmation)

    except Exception as e:
        logger.error(f"Error processing voice message: {e}")
        await message.answer("خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

@router.callback_query(F.data == "confirm_voice_text")
async def confirm_voice_transcription(callback: CallbackQuery, state: FSMContext):
    """Handle confirmation of voice transcription"""
    try:
        data = await state.get_data()
        voice_transcript = data.get('voice_transcript', '')

        if not voice_transcript:
            await callback.answer("خطا: متن صوتی یافت نشد.")
            return

        await callback.message.edit_text(
            f"✅ متن تأیید شد: \"{voice_transcript}\"\n\nچه نوع محتوایی می‌خواید تولید کنید؟",
            reply_markup=get_content_type_keyboard()
        )

        # Store the transcript as input text and move to content selection
        await state.update_data(user_input=voice_transcript)
        await state.set_state(ContentGeneration.waiting_for_content_type)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error confirming voice transcription: {e}")
        await callback.answer("خطایی رخ داده است.")

@router.callback_query(F.data == "cancel_voice")
async def cancel_voice_transcription(callback: CallbackQuery, state: FSMContext, user_service: UserService):
    """Handle cancellation of voice transcription"""
    try:
        user = await user_service.get_or_create_user(telegram_id=callback.from_user.id)
        subscription = await user_service.get_user_subscription(user.id)
        is_subscribed = subscription.is_active if subscription else False

        await callback.message.edit_text("عملیات لغو شد.")
        await callback.message.answer(
            "چه کاری می‌تونم برای شما انجام بدهم؟",
            reply_markup=get_main_menu(is_subscribed)
        )
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Error canceling voice transcription: {e}")
        await callback.answer("خطایی رخ داده است.")


# Utility handlers
@router.message(F.text == "🔙 بازگشت")
async def back_to_main_menu(message: Message, state: FSMContext, user_service: UserService):
    """Return to main menu"""
    try:
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

🎤 قابلیت جدید - پیام صوتی:
• می‌توانید به جای تایپ، پیام صوتی ارسال کنید
• تبدیل صدا به متن فارسی با کیفیت بالا
• پشتیبانی از تمام لهجه‌های فارسی

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

def register_handlers() -> Router:
    """Register all handlers and return router"""
    return router