"""
Financial Coach Agent

An AI-powered financial coaching agent that provides personalized
financial guidance and retirement planning advice.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from app.schemas.agent_schemas import (
    AgentRecommendation,
    CoachConversation,
    CoachMessage,
    PersonalFinancialProfile,
    RetirementReadinessResult,
)
from app.services.retirement_readiness_service import RetirementReadinessService


class CoachTopic(str, Enum):
    """Topics the financial coach can address."""

    RETIREMENT = "retirement"
    INVESTMENT = "investment"
    BUDGETING = "budgeting"
    EMERGENCY_FUND = "emergency_fund"
    DEBT_MANAGEMENT = "debt_management"
    TAX_PLANNING = "tax_planning"
    INSURANCE = "insurance"
    ESTATE_PLANNING = "estate_planning"
    GENERAL = "general"


class FinancialCoachAgent:
    """AI Financial Coach that provides personalized financial guidance."""

    # Pre-built advice templates by topic
    RETIREMENT_ADVICE = {
        "on_track": [
            "你的退休規劃進展良好！目前的儲蓄進度符合預期。",
            "建議持續保持目前的儲蓄率，並定期檢視投資組合配置。",
            "考虑在條件允許時提高勞退自提比例，以享受稅收優惠。",
        ],
        "moderate_gap": [
            "你的退休規劃有些微缺口，但仍有時間改善。",
            "建議檢視每月支出，設法提高儲蓄率至少5-10%。",
            "可考慮延長工作年限或調整退休後的生活預期。",
        ],
        "significant_gap": [
            "你的退休儲蓄缺口較大，需要積極採取行動。",
            "建議立即提高儲蓄率至收入的20%以上，並檢視所有非必要支出。",
            "可考慮增加收入來源或延後退休計劃。",
        ],
        "off_track": [
            "你的退休規劃偏離軌道，需要大幅調整財務策略。",
            "建議尋求專業財務顧問協助，制定詳細的追趕計劃。",
            "同時檢視是否能增加收入或減少支出，以加快儲蓄速度。",
        ],
    }

    BUDGETING_ADVICE = [
        "建議採用50/30/20預算法則：50%需求支出、30%想要支出、20%儲蓄與債務。",
        "追蹤每月支出是理財的第一步，建議使用應用程式記錄所有開支。",
        "每月的非必要性支出（如餐飲、娛樂）建議控制在收入的30%以內。",
    ]

    def __init__(self, user_id: str, profile: Optional[PersonalFinancialProfile] = None):
        self.user_id = user_id
        self.profile = profile
        self.conversation = CoachConversation(
            user_id=user_id,
            messages=[],
        )
        self.readiness_service = RetirementReadinessService()

    def add_user_message(self, content: str, topic: Optional[str] = None) -> CoachMessage:
        """Add a user message to the conversation."""
        message = CoachMessage(
            message_id=uuid.uuid4(),
            role="user",
            content=content,
            topic=topic or self._detect_topic(content),
            created_at=datetime.utcnow(),
        )
        self.conversation.messages.append(message)
        self.conversation.updated_at = datetime.utcnow()
        return message

    def generate_coach_response(
        self,
        readiness_result: Optional[RetirementReadinessResult] = None,
    ) -> CoachMessage:
        """Generate the coach's response based on conversation context."""
        last_message = self.conversation.messages[-1] if self.conversation.messages else None

        if not last_message:
            content = "你好！我是你的AI財務教練。你可以問我關於退休規劃、投資、預算管理等方面的問題。我會根據你的財務狀況提供個人化的建議。"
        else:
            content = self._generate_topic_response(last_message.topic, readiness_result)

        coach_message = CoachMessage(
            message_id=uuid.uuid4(),
            role="coach",
            content=content,
            topic=last_message.topic if last_message else CoachTopic.GENERAL,
            created_at=datetime.utcnow(),
        )
        self.conversation.messages.append(coach_message)
        self.conversation.current_focus = coach_message.topic
        self.conversation.updated_at = datetime.utcnow()
        return coach_message

    def _generate_topic_response(
        self,
        topic: Optional[str],
        readiness_result: Optional[RetirementReadinessResult],
    ) -> str:
        """Generate response based on detected topic."""
        if topic == CoachTopic.RETIREMENT or topic == "retirement":
            return self._retirement_response(readiness_result)
        elif topic == CoachTopic.BUDGETING or topic == "budgeting":
            return self._budgeting_response()
        elif topic == CoachTopic.INVESTMENT or topic == "investment":
            return self._investment_response()
        elif topic == CoachTopic.EMERGENCY_FUND or topic == "emergency_fund":
            return self._emergency_fund_response()
        elif topic == CoachTopic.DEBT_MANAGEMENT or topic == "debt_management":
            return self._debt_response()
        else:
            return self._general_response()

    def _retirement_response(self, readiness: Optional[RetirementReadinessResult]) -> str:
        """Generate retirement-specific response."""
        if readiness:
            level_advice = self.RETIREMENT_ADVICE.get(readiness.readiness_level, self.RETIREMENT_ADVICE["moderate_gap"])
            advice = "\n".join(f"• {a}" for a in level_advice)

            return (
                f"根據你的財務狀況，我对你的退休準備度評分為 **{readiness.readiness_score:.0f}/100**（{self._level_display(readiness.readiness_level)}）。\n\n"
                f"📊 現況分析：\n"
                f"• 目前退休儲蓄：NT${readiness.current_nest_egg:,.0f}\n"
                f"• 建議目標：NT${readiness.on_track_nest_egg:,.0f}\n"
                f"• 距離退休：{readiness.years_to_retirement} 年\n\n"
                f"💡 建議：\n{advice}\n\n"
                f"如需更詳細的退休規劃建議，請提供更多關於你的收支和投資組合資訊。"
            )
        else:
            return (
                "要評估你的退休規劃，我需要了解一些基本資訊：\n"
                "• 你的年齡和預期退休年齡\n"
                "• 目前的退休儲蓄金額\n"
                "• 每月能儲蓄的金額\n"
                "• 退休後的預期每月支出\n\n"
                "提供這些資訊後，我可以為你進行更精準的退休準備度評估。"
            )

    def _budgeting_response(self) -> str:
        """Generate budgeting advice."""
        advice = "\n".join(f"• {a}" for a in self.BUDGETING_ADVICE)
        return (
            "良好的預算管理是財務健康的基礎。\n\n"
            "💰 實用建議：\n"
            f"{advice}\n\n"
            "如需個人化的預算建議，請告訴我你每月的收入和支出概況。"
        )

    def _investment_response(self) -> str:
        """Generate investment advice."""
        if not self.profile:
            return "要給你適當的投資建議，我需要了解你的年齡、風險承受度和投資目標。請告訴我這些基本資訊。"

        risk_responses = {
            "conservative": "根據你的穩健型風險偏好，建議以债券和定存為主，輔以少部分藍籌股或ETF。可考慮「股四債六」的配置。",
            "moderate": "根據你的適中型風險偏好，建議「股六債四」配置，核心持有大盤ETF如VT或VTI，搭配部分成長型股票。",
            "aggressive": "根據你的積極型風險偏好，你可以承受較高的股債比例（8:2或更高），建議以成長股和新興市場ETF為主。",
        }
        base = risk_responses.get(self.profile.risk_tolerance or "moderate", risk_responses["moderate"])

        return (
            f"{base}\n\n"
            "📈 基本原則：\n"
            "• 分散投資，不要把所有資金放在單一股票\n"
            "• 定期定額投資，紀律比時機重要\n"
            "• 長期持有，避免頻繁交易\n"
            "• 每年檢視並 rebalance 一次\n\n"
            "如有特定投資問題，歡迎繼續詢問！"
        )

    def _emergency_fund_response(self) -> str:
        """Generate emergency fund advice."""
        return (
            "緊急備用金是財務安全的基礎。\n\n"
            "💵 建議原則：\n"
            "• 金額：至少 3-6 個月的生活費用\n"
            "• 存放：選擇高收益儲蓄帳戶或貨幣市場基金，流动性要好\n"
            "• 不要投資在股票或债券中，緊急時可能需要變現\n\n"
            "建議先建立緊急備用金，再考慮其他投資或退休儲蓄。"
        )

    def _debt_response(self) -> str:
        """Generate debt management advice."""
        return (
            "有效的債務管理對財務健康至關重要。\n\n"
            "💳 建議策略：\n"
            "• 信用卡債：務必按時全額繳款，避免高利率滾動\n"
            "• 學貸/車貸：按部就班償還，可考慮雪崩法（先還高利率）\n"
            "• 房貸：視利率決定提前還款優先級\n\n"
            "如有具體債務情況，請告訴我，我可以提供更針對性的建議。"
        )

    def _general_response(self) -> str:
        """Generate a general response."""
        return (
            "感謝你的提問！我是你的AI財務教練，可以幫助你：\n\n"
            "• 🏖️ **退休規劃** — 評估退休準備度、缺口分析\n"
            "• 💰 **預算管理** — 制定預算、控制支出\n"
            "• 📈 **投資建議** — 資產配置、投資組合建議\n"
            "• 🏦 **緊急備用金** — 建立財務安全網\n"
            "• 💳 **債務管理** — 信用卡、學貸等債務策略\n\n"
            "請告訴我最想了解哪個方面，我可以提供更詳細的建議。"
        )

    def _detect_topic(self, content: str) -> str:
        """Detect the topic of user message."""
        content_lower = content.lower()

        if any(k in content_lower for k in ["退休", "retire", "養老", "退休金", "retirement"]):
            return CoachTopic.RETIREMENT
        elif any(k in content_lower for k in ["預算", "預算", "支出", "花費", "budget", "expense", "花費"]):
            return CoachTopic.BUDGETING
        elif any(k in content_lower for k in ["投資", "股票", "基金", "ETF", "invest", "stock", "portfolio"]):
            return CoachTopic.INVESTMENT
        elif any(k in content_lower for k in ["緊急", "備用金", "emergency", "savings"]):
            return CoachTopic.EMERGENCY_FUND
        elif any(k in content_lower for k in ["債務", "貸款", "信用卡", "debt", "loan", "credit"]):
            return CoachTopic.DEBT_MANAGEMENT
        else:
            return CoachTopic.GENERAL

    def _level_display(self, level: str) -> str:
        """Convert readiness level to display string."""
        displays = {
            "on_track": "進展良好 ✅",
            "moderate_gap": "有些微缺口 ⚠️",
            "significant_gap": "缺口較大 ⚠️⚠️",
            "off_track": "嚴重偏離 🚨",
        }
        return displays.get(level, level)

    def get_conversation(self) -> CoachConversation:
        """Get the current conversation."""
        return self.conversation

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation = CoachConversation(user_id=self.user_id, messages=[])
