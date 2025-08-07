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
        """Generate Instagram Reels scenarios"""
        style_prompt = self._get_style_prompt(user_profile.page_style)
        audience_prompt = self._get_audience_prompt(user_profile.audience_type)
        
        system_prompt = f"""
        تو یک کارگردان محتوا برای ریلز اینستاگرام هستی که برای صفحات طلا و جواهرات کار می‌کنی.
        
        سبک محتوا: {style_prompt}
        مخاطب هدف: {audience_prompt}
        
        قوانین:
        - 3 سناریو مختلف ارائه بده
        - هر سناریو شامل: موضوع، چگونگی فیلم‌برداری، متن روی ویدیو، موزیک پیشنهادی
        - سناریوها باید قابل اجرا و عملی باشند
        - از ترندهای روز استفاده کن
        - هر سناریو را با عدد شماره‌گذاری کن
        """
        
        user_prompt = f"""
        موضوع اصلی: {theme}
        {f"مناسبت: {occasion}" if occasion else ""}
        
        لطفاً 3 سناریو ریلز مختلف ارائه بده.
        """
        
        try:
            response = await self._call_ai(system_prompt, user_prompt)
            scenarios = self._parse_numbered_content(response, 3)
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
            response = await self._call_ai(system_prompt, user_prompt)
            ideas = self._parse_numbered_content(response, 3)
            return ideas
        except Exception as e:
            logger.error(f"Error generating visual ideas: {e}")
            return ["خطا در تولید ایده بصری. لطفاً دوباره تلاش کنید."]

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