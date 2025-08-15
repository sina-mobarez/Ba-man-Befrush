import openai
from typing import List, Optional
import logging
from core.config import settings
from models.schema import UserProfile, PageStyle, AudienceType, SalesGoal

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        """
        Initializes the AI service with the modern OpenAI client.
        """
        # MODIFIED: Create an instance of the AsyncOpenAI client
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        logger.info("AIService initialized with OpenRouter client.")
        self.last_prompt_name: Optional[str] = None
        self.last_prompt_content: Optional[str] = None

    async def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """
        Calls the OpenRouter AI API using the modern openai>=1.0.0 syntax.
        """
        try:
            response = await self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}", exc_info=True)
            raise

    async def generate_caption(
        self,
        product_description: str,
        user_profile: UserProfile,
        additional_context: Optional[str] = None
    ) -> List[str]:
        """Generate 3 captions for a product"""
        style_prompt = self._get_style_prompt(user_profile.page_style)
        audience_prompt = self._get_audience_prompt(user_profile.audience_type)
        goal_prompt = self._get_goal_prompt(user_profile.sales_goal)

        system_prompt = f"""
        تو یک متخصص بازاریابی طلا و جواهرات هستی که برای صفحات اینستاگرام فارسی کپشن می‌نویسی.
        
        سبک نوشتن: {style_prompt}
        نوع مخاطب: {audience_prompt}
        هدف اصلی: {goal_prompt}
        
        {f"اطلاعات کسب‌وکار: {user_profile.business_name} - {user_profile.business_description}" if user_profile.business_name else ""}
        
        قوانین:
        - حتماً 3 کپشن مختلف بنویس
        - هر کپشن را با عدد شماره‌گذاری کن
        - از ایموجی مناسب استفاده کن
        - CTA (فراخوان عمل) در پایان هر کپشن بیاور
        - کپشن‌ها باید جذاب و متقاعدکننده باشند
        - زبان فارسی روان و طبیعی استفاده کن
        """
        
        user_prompt = f"""
        محصول: {product_description}
        {f"توضیحات اضافی: {additional_context}" if additional_context else ""}
        
        لطفاً 3 کپشن مختلف برای این محصول بنویس.
        """

        try:
            self.last_prompt_name = "caption_generation"
            self.last_prompt_content = f"SYSTEM:\n{system_prompt.strip()}\n\nUSER:\n{user_prompt.strip()}"
            response = await self._call_ai(system_prompt, user_prompt)
            captions = self._parse_numbered_content(response, 3)
            return captions
        except Exception as e:
            logger.error(f"Error generating captions: {e}")
            return ["خطا در تولید کپشن. لطفاً دوباره تلاش کنید."]
    
    async def generate_reels_scenario(
        self,
        theme: str,
        user_profile: UserProfile,
        occasion: Optional[str] = None
    ) -> List[str]:
        """Generate Instagram Reels scenarios with enhanced prompt engineering"""
        style_prompt = self._get_style_prompt(user_profile.page_style)
        audience_prompt = self._get_audience_prompt(user_profile.audience_type)
        
        system_prompt = f"""
        تو یک کارگردان محتوای اینستاگرام حرفه‌ای و خبره هستی که مختص طلا و جواهرات کار می‌کنی. 
        تخصص اصلی‌ت تولید سناریوهای ریلز ویرال و جذاب است.
        
        سبک محتوای مورد نظر: {style_prompt}
        مخاطب هدف: {audience_prompt}
        نام گالری: {user_profile.gallery_name or 'گالری کاربر'}
        اینستاگرام: {user_profile.instagram_handle or 'instagram_handle'}
        
        ⚠️ قوانین سخت‌گیرانه تولید سناریو:
        1. حتماً 3 سناریو کاملاً مختلف و مجزا تولید کن
        2. هر سناریو را دقیقاً با این فرمت شروع کن: "سناریو ۱:" یا "سناریو ۲:" یا "سناریو ۳:"
        3. هر سناریو باید دارای این بخش‌های مجزا باشد:
           📋 موضوع ریلز
           🎬 نحوه فیلم‌برداری (زاویه، حرکات دوربین، تکنیک‌ها)
           ✍️ متن روی ویدیو (Text Overlay)
           🎵 نوع موزیک پیشنهادی
           ⏱️ مدت زمان (15-30 ثانیه)
           🎯 هدف (engagement, sales, awareness)
           
        4. زبان فارسی روان و عاری از اشتباه املایی
        5. سناریوها باید عملی، قابل اجرا و مقرون‌به‌صرفه باشند
        6. از ترندهای اینستاگرام و تکنیک‌های ویرال استفاده کن
        7. مناسب برند طلا و جواهرات باشد
        """
        
        user_prompt = f"""
        موضوع اصلی: {theme}
        {f"مناسبت: {occasion}" if occasion else ""}
        مشتریان اصلی: {user_profile.main_customers or 'عموم'}
        
        حالا 3 سناریو ریلز کاملاً حرفه‌ای و عملی برای این موضوع تولید کن.
        هر سناریو را با "سناریو ۱:", "سناریو ۲:", "سناریو ۳:" شروع کن.
        """
        
        try:
            self.last_prompt_name = "reels_generation"
            self.last_prompt_content = f"SYSTEM:\n{system_prompt.strip()}\n\nUSER:\n{user_prompt.strip()}"
            response = await self._call_ai(system_prompt, user_prompt)
            scenarios = self._parse_persian_numbered_content(response, 3)
            return scenarios
        except Exception as e:
            logger.error(f"Error generating reels scenarios: {e}")
            return ["خطا در تولید سناریو ریلز. لطفاً دوباره تلاش کنید."]

    async def generate_visual_ideas(
        self,
        product_type: str,
        user_profile: UserProfile,
        available_props: Optional[str] = None
    ) -> List[str]:
        """Generate visual ideas for photography"""
        style_prompt = self._get_style_prompt(user_profile.page_style)
        
        system_prompt = f"""
        تو یک عکاس حرفه‌ای طلا و جواهرات هستی که ایده‌های بصری خلاقانه ارائه می‌دهی.
        
        سبک مطلوب: {style_prompt}
        
        قوانین:
        - 3 ایده بصری مختلف ارائه بده
        - هر ایده شامل: زاویه عکس، نورپردازی، چیدمان، پس‌زمینه
        - ایده‌ها باید با امکانات موجود قابل اجرا باشند
        - نکات فنی عکاسی را هم بگو
        - هر ایده را با عدد شماره‌گذاری کن
        """
        
        user_prompt = f"""
        نوع محصول: {product_type}
        {f"وسایل موجود: {available_props}" if available_props else ""}
        
        لطفاً 3 ایده بصری مختلف برای عکس‌برداری ارائه بده.
        """
        
        try:
            self.last_prompt_name = "visual_ideas_generation"
            self.last_prompt_content = f"SYSTEM:\n{system_prompt.strip()}\n\nUSER:\n{user_prompt.strip()}"
            response = await self._call_ai(system_prompt, user_prompt)
            ideas = self._parse_numbered_content(response, 3)
            return ideas
        except Exception as e:
            logger.error(f"Error generating visual ideas: {e}")
            return ["خطا در تولید ایده بصری. لطفاً دوباره تلاش کنید."]

    async def generate_situation_summary(self, user_profile: UserProfile) -> str:
        """Generate Persian situation summary from collected onboarding info"""
        system_prompt = (
            "تو یک مشاور حرفه‌ای در زمینه بازاریابی و استراتژی محتوا برای طلافروشان هستی. "
            "بر اساس اطلاعات کاربر، یک تحلیل ساختاریافته و کاربردی به زبان فارسی ارائه بده که شامل بخش‌های زیر باشد:\n"
            "1. تحلیل وضعیت فعلی (نقاط قوت و ضعف)\n"
            "2. پیشنهادات عملی برای بهبود\n"
            "3. شناخت مخاطبان هدف\n"
            "4. راهکارهای محتوایی\n\n"
            "رعایت این نکات ضروری است:\n"
            "- از عناوین شماره‌دار و نشانه‌گذاری ساده استفاده کن\n"
            "- از علامت‌هایی مانند #، *، - در ابتدای خطوط خودداری کن\n"
            "- لحن حرفه‌ای ولی قابل فهم و دوستانه داشته باش\n"
            "- پیشنهادات باید عملی و متناسب با کسب‌وکار طلا باشد\n"
            "- جملات کوتاه و گویا باشند"
        )
        user_prompt = (
            f"اطلاعات کسب‌وکار:\n"
            f"نام گالری: {user_profile.gallery_name}\n"
            f"صفحه اینستاگرام: {user_profile.instagram_handle or 'ثبت نشده'}\n"
            f"کانال تلگرام: {user_profile.telegram_channel or 'ثبت نشده'}\n"
            f"مشتریان اصلی: {user_profile.main_customers}\n"
            f"محدودیت‌ها و بایدونبایدها: {user_profile.constraints_and_guidelines}\n"
            f"نیازهای محتوایی: {user_profile.content_help}\n"
            f"فروشگاه فیزیکی: {'دارد' if user_profile.has_physical_store else 'ندارد'}\n"
            f"اطلاعات تکمیلی: {user_profile.additional_info or 'ثبت نشده'}\n\n"
            f"لطفاً تحلیل کاملی ارائه دهید:"
        )
        try:
            self.last_prompt_name = "situation_summary"
            self.last_prompt_content = f"SYSTEM:\n{system_prompt.strip()}\n\nUSER:\n{user_prompt.strip()}"
            return await self._call_ai(system_prompt, user_prompt)
        except Exception:
            return "خلاصه وضعیت آماده نشد. بعداً دوباره تلاش کنید."

    async def generate_content_calendar(self, user_profile: UserProfile) -> List[str]:
        """Generate a short 3-item content calendar suggestion"""
        system_prompt = (
            "تو یک برنامه‌ریز محتوا هستی. بر اساس اطلاعات زیر 3 ایده محتوایی زمان‌بندی شده بده."
        )
        user_prompt = (
            f"مخاطب: {user_profile.main_customers}\n"
            f"محدودیت‌ها: {user_profile.constraints_and_guidelines}\n"
            f"سبک صفحه: {self._get_style_prompt(user_profile.page_style)}\n"
        )
        try:
            self.last_prompt_name = "content_calendar"
            self.last_prompt_content = f"SYSTEM:\n{system_prompt.strip()}\n\nUSER:\n{user_prompt.strip()}"
            response = await self._call_ai(system_prompt, user_prompt)
            return self._parse_numbered_content(response, 3)
        except Exception:
            return ["خطا در تولید تقویم."]

    def _parse_numbered_content(self, content: str, expected_count: int) -> List[str]:
        """Parse numbered content from AI response"""
        lines = content.strip().split('\n')
        parsed_content = []
        current_item = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '۱.', '۲.', '۳.')):
                if current_item:
                    parsed_content.append(current_item.strip())
                current_item = line
            elif current_item:
                current_item += f"\n{line}"
        
        if current_item:
            parsed_content.append(current_item.strip())
        
        if len(parsed_content) < expected_count:
            chunks = content.split('\n\n')
            parsed_content = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        return parsed_content[:expected_count] if parsed_content else [content]
    
    def _parse_persian_numbered_content(self, content: str, expected_count: int) -> List[str]:
        """Parse Persian numbered content specifically for reels scenarios"""
        # Clean up the content
        content = content.strip()
        
        # Split by Persian scenario markers
        scenarios = []
        
        # Look for Persian scenario markers
        import re
        scenario_pattern = r'سناریو\s*[۱۲۳123]\s*:'
        
        parts = re.split(scenario_pattern, content, flags=re.IGNORECASE)
        
        # The first part might be empty or contain intro text
        if len(parts) > 1:
            for i in range(1, len(parts)):
                scenario_text = parts[i].strip()
                if scenario_text:
                    # Add the scenario header back
                    scenario_num = i
                    persian_nums = ['', '۱', '۲', '۳']
                    if scenario_num <= 3:
                        full_scenario = f"سناریو {persian_nums[scenario_num]}:\n{scenario_text}"
                        scenarios.append(full_scenario)
        
        # Fallback to original parsing if no scenarios found
        if not scenarios:
            return self._parse_numbered_content(content, expected_count)
        
        # Ensure we have exactly the expected count
        if len(scenarios) < expected_count:
            # Split the content differently as fallback
            chunks = content.split('\n\n')
            scenarios = [chunk.strip() for chunk in chunks if chunk.strip() and 'سناریو' in chunk]
        
        return scenarios[:expected_count] if scenarios else [content]
    
    def _get_style_prompt(self, style: PageStyle) -> str:
        """Get style-specific prompt"""
        style_prompts = {
            PageStyle.SERIOUS: "رسمی، حرفه‌ای و معتبر",
            PageStyle.FRIENDLY: "دوستانه، صمیمی و نزدیک به مشتری", 
            PageStyle.LUXURY: "لوکس، مجلل و اشرافی",
            PageStyle.TRADITIONAL: "سنتی، اصیل و فرهنگی"
        }
        return style_prompts.get(style, "دوستانه و طبیعی")
    
    def _get_audience_prompt(self, audience: AudienceType) -> str:
        """Get audience-specific prompt"""
        audience_prompts = {
            AudienceType.YOUTH: "جوانان و نسل جدید",
            AudienceType.LUXURY: "مشتریان لاکچری و پولdar",
            AudienceType.BRIDES: "عروس‌خانم‌ها و زوج‌های جوان",
            AudienceType.GENERAL: "عموم مردم"
        }
        return audience_prompts.get(audience, "عموم مردم")

    def _get_goal_prompt(self, goal: SalesGoal) -> str:
        """Get goal-specific prompt"""
        goal_prompts = {
            SalesGoal.INCREASE_SALES: "افزایش فروش و تبدیل مخاطب به مشتری",
            SalesGoal.BRAND_AWARENESS: "افزایش آگاهی از برند و شناخت",
            SalesGoal.ENGAGEMENT: "افزایش تعامل و لایک و کامنت"
        }
        return goal_prompts.get(goal, "افزایش فروش")