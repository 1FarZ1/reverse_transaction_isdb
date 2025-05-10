
import streamlit as st
import json
import re
import os
from typing import Dict, List
import numpy as np
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory

from openai import OpenAI


from langchain.tools import BaseTool
from typing import Optional
from langchain.prompts import ChatPromptTemplate
from langchain.schema.messages import SystemMessage, HumanMessage


# client = OpenAI(api_key='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')
EXAMPLE_ENTRIES = {
    "FAS 4 - Mudarabah": """
Context: GreenTech exits in Year 3, and Al Baraka Bank buys out its stake.
Adjustments:
Buyout Price: $1,750,000
Bank Ownership: 100%

Journal Entry for Buyout:
Dr. GreenTech Equity $1,750,000
Cr. Cash $1,750,000
""",
    "FAS 7 - Salam": """
Context: Al Baraka Bank enters into a Salam contract with a farmer for 5 tons of wheat.
Adjustments:
Salam Capital: $50,000
Delivery Date: 6 months later

Journal Entry:
Dr. Salam Asset (Wheat) $50,000
Cr. Cash $50,000
""",
    "FAS 10 - Istisna'a": """
Context: Al Baraka Bank contracts construction company to build a commercial building.
Adjustments:
Contract Value: $2,500,000
Current Progress: 40% complete

Journal Entry:
Dr. Work-in-Progress Asset $1,000,000
Cr. Progress Payments Liability $1,000,000
""",
    "FAS 20 - Deferred Payment Sale": """
Context: Al Baraka Bank sells equipment to customer with deferred payment plan.
Adjustments:
Cost of Equipment: $75,000
Markup: $15,000
Payment Terms: 24 monthly installments

Journal Entry:
Dr. Murabaha Receivables $90,000
Cr. Inventory $75,000
Cr. Deferred Profit $15,000
""",
    "FAS 28 - Ijarah": """
Context: Al Baraka Bank leases office space to client for 5 years.
Adjustments:
Right-of-use Asset Value: $500,000
Annual Rental: $120,000

Journal Entry:
Dr. Ijarah Asset $500,000
Cr. Cash $500,000

Dr. Cash $120,000
Cr. Ijarah Revenue $120,000
""",
    "FAS 32 - Investment": """
Context: Al Baraka Bank acquires 25% stake in emerging tech company.
Adjustments:
Investment Amount: $5,000,000
Expected Annual Return: 8%

Journal Entry:
Dr. Equity Investment $5,000,000
Cr. Cash $5,000,000
"""
}
# Load AAOIFI FAS Standards (same as original)
FAS_STANDARDS = {
    "FAS 4": {
        "name": "Mudarabah Financing",
        "summary": """
        FAS 4 deals with Mudarabah financing, which is a partnership where one party 
        provides capital (Rab al-Mal) and the other provides expertise (Mudarib).
        Key features:
        - Recognition of capital provided
        - Profit sharing between capital provider and manager
        - Treatment of losses (borne by capital provider)
        - Equity accounting for investments
        - Exit and buyout procedures
        """,
        "keywords": ["mudarabah", "partnership", "equity", "capital", "profit sharing", 
                   "buyout", "investment", "exit", "stakeholder", "ownership"]
    },
    "FAS 7": {
        "name": "Salam and Parallel Salam",
        "summary": """
        FAS 7 covers Salam transactions, which involve advance payment for deferred delivery 
        of goods. Key features:
        - Recognition of Salam capital (advance payment)
        - Measurement of Salam assets
        - Delivery and settlement procedures
        - Parallel Salam transactions
        """,
        "keywords": ["salam", "advance payment", "deferred delivery", "goods", 
                   "parallel salam", "inventory", "commodity"]
    },
    "FAS 10": {
        "name": "Istisna'a and Parallel Istisna'a",
        "summary": """
        FAS 10 addresses Istisna'a contracts, which involve manufacturing or construction 
        with progress payments. Key features:
        - Recognition of work-in-progress
        - Revenue recognition for long-term contracts
        - Cost accounting for manufacturing/construction
        - Change orders and contract modifications
        - Progress payments and billing
        """,
        "keywords": ["istisna'a", "manufacturing", "construction", "work-in-progress", 
                   "progress payments", "contract", "change order", "project", 
                   "reversal", "billing"]
    },
    "FAS 20": {
        "name": "Deferred Payment Sale",
        "summary": """
        FAS 20 covers Murabaha and other deferred payment sales. Key features:
        - Recognition of cost plus markup
        - Deferred profit recognition
        - Installment accounting
        - Early settlement discounts
        """,
        "keywords": ["murabaha", "deferred payment", "installment", "profit", "sale", 
                   "markup", "discount", "settlement"]
    },
    "FAS 28": {
        "name": "Ijarah",
        "summary": """
        FAS 28 addresses Ijarah (lease) accounting including Ijarah Muntahia Bittamleek (IMB).
        Key features:
        - Right-of-use asset recognition
        - Ijarah liability measurement
        - Rental payments
        - Residual value treatment
        - Transfer of ownership options
        """,
        "keywords": ["ijarah", "lease", "rental", "right-of-use", "asset", "liability", 
                   "amortization", "transfer", "ownership"]
    },
    "FAS 32": {
        "name": "Investment in Sukuk, Shares and Similar Instruments",
        "summary": """
        FAS 32 covers investment classification, measurement, and disclosure. Key features:
        - Classification of investments (monetary, non-monetary)
        - Fair value vs. historical cost accounting
        - Equity method accounting
        - Investment exit and disposal
        - Investment income recognition
        """,
        "keywords": ["investment", "sukuk", "shares", "equity", "fair value", "exit", 
                   "disposal", "monetary", "income", "acquisition"]
    }
}


system_prompt = SystemMessage(
    content="You are an expert in Islamic finance and AAOIFI standards. "
            "Your job is to analyze journal entries, identify which FAS standards they relate to, "
            "and check Sharia compliance. When analyzing, extract the accounts, amounts, context, "
            "and relevant financial details."
)


human_prompt = HumanMessage(
    content="{input}\n\n{agent_scratchpad}"  # Add agent_scratchpad here
)


from langchain.prompts import MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import MessagesPlaceholder, HumanMessagePromptTemplate

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are an expert in Islamic finance and AAOIFI standards. "
            "Your job is to analyze journal entries, identify which FAS standards they relate to, "
            "and check Sharia compliance. When analyzing, extract the accounts, amounts, context, "
            "and relevant financial details"),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    HumanMessagePromptTemplate.from_template("{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])
class FASLookupTool(BaseTool):
    name: str = "fas_standard_lookup"
    description: str = "Look up detailed AAOIFI FAS standards and their requirements"

    def _run(self, fas_id: str) -> str:
        return json.dumps(FAS_STANDARDS.get(fas_id, {}))

    def _arun(self, fas_id: str) -> str:
        raise NotImplementedError("Async not supported")

class ShariaComplianceTool(BaseTool):
    name: str = "sharia_compliance_check"
    description: str = "Verify compliance with AAOIFI Sharia Standards (SS)"

    def _run(self, entry_data: dict) -> dict:
        return {"is_compliant": True, "issues": [], "references": ["SS 1", "SS 5"]}

    def _arun(self, entry_data: dict) -> dict:
        raise NotImplementedError("Async not supported")

class AAOIFIAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.8,api_key=os.getenv("OPENAI_API_KEY"))
        self.tools = [FASLookupTool(), ShariaComplianceTool()]
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.agent = create_openai_tools_agent(
            self.llm, 
            self.tools, 
            prompt=prompt_template,
        )
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, memory=self.memory, verbose=True, return_intermediate_steps=True)

    def parse_journal_entry(self, entry: str) -> Dict:
        debit_pattern = r"Dr\.?\s+([^$]+)\s+\$([0-9,]+(?:\.[0-9]+)?)"
        credit_pattern = r"Cr\.?\s+([^$]+)\s+\$([0-9,]+(?:\.[0-9]+)?)"
        debits = [{"account": m.group(1).strip(), "amount": float(m.group(2).replace(',', ''))} for m in re.finditer(debit_pattern, entry)]
        credits = [{"account": m.group(1).strip(), "amount": float(m.group(2).replace(',', ''))} for m in re.finditer(credit_pattern, entry)]
        context = re.search(r"Context:\s+(.+?)(?=\n\n|\Z)", entry, re.DOTALL)
        adjustments = re.search(r"Adjustments:\s+(.+?)(?=\n\n|\Z)", entry, re.DOTALL)
        return {
            "debits": debits,
            "credits": credits,
            "context": context.group(1).strip() if context else "",
            "adjustments": adjustments.group(1).strip() if adjustments else "",
            "full_entry": entry
        }

    def analyze_entry(self, entry: str) -> dict:
        parsed = self.parse_journal_entry(entry)
        # Mock agent output
        return {
            "parsed_data": parsed,
            "results": [
                {"fas_id": "FAS 4", "name": "Mudarabah", "score": 0.82, "confidence": "High", "explanation": "Equity involved in transaction", "matched_keywords": ["equity", "buyout"]},
                {"fas_id": "FAS 32", "name": "Investment", "score": 0.65, "confidence": "Medium", "explanation": "Investment pattern", "matched_keywords": ["investment"]}
            ],
            "sharia_status": {"is_compliant": True, "issues": [], "references": ["SS 1", "SS 5"]}
        }

def main():
    st.set_page_config(page_title="AAOIFI Agent", layout="wide")
    st.title("AAOIFI FAS Analyzer (Agentic AI Version)")
    tab1, tab2 = st.tabs(["Analyze Entry", "View FAS Standards"])

    with tab1:
        st.sidebar.header("Example Entries")
        example = st.sidebar.selectbox("Select Example", list(EXAMPLE_ENTRIES.keys()))
        if st.sidebar.button("Load Example"):
            journal_entry = EXAMPLE_ENTRIES[example]
        else:
            journal_entry = ""

        journal_input = st.text_area("Enter Journal Entry", value=journal_entry, height=250)
        if st.button("Analyze"):
            agent = AAOIFIAgent()
            result = agent.analyze_entry(journal_input)
            print(result)

            parsed = result["parsed_data"]
            st.subheader("Parsed Journal Entry")
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Context**")
                    st.info(parsed["context"] or "-")
                    st.markdown("**Adjustments**")
                    st.info(parsed["adjustments"] or "-")
                with col2:
                    st.markdown("**Debits**")
                    if parsed["debits"]:
                        st.table(parsed["debits"])
                    else:
                        st.write("-")
                    st.markdown("**Credits**")
                    if parsed["credits"]:
                        st.table(parsed["credits"])
                    else:
                        st.write("-")

# --- Top FAS Matches Section ---
            st.subheader("Top FAS Matches")
            for i, res in enumerate(result["results"]):
                with st.expander(f"{i+1}. {res['fas_id']} - {res['name']} (Confidence: {res['confidence']})", expanded=(i==0)):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        # Confidence badge
                        confidence_color = {
                            "High": "green",
                            "Medium": "orange",
                            "Low": "red"
                        }.get(res["confidence"], "gray")
                        st.markdown(
                            f"<div style='display:inline-block;background:{confidence_color};"
                            "color:white;padding:6px 18px;border-radius:8px;font-weight:bold;"
                            "margin-bottom:8px;'>"
                            f"{res['confidence']}</div>",
                            unsafe_allow_html=True
                        )
                        st.metric("Score", f"{res['score']*100:.1f}%")
                    with col2:
                        st.markdown("**Explanation**")
                        st.write(res["explanation"])
                        st.markdown("**Matched Keywords**")
                        st.markdown(
                            " ".join(
                                f"<span style='background: #e0e7ff; color: #3730a3; "
                                "padding:3px 10px;border-radius:6px;margin-right:4px;font-size:90%;"
                                "font-weight:500;'>{kw}</span>"
                                for kw in res["matched_keywords"]
                            ),
                            unsafe_allow_html=True
                        )
                        # Show FAS summary if available
                        fas_info = FAS_STANDARDS.get(res["fas_id"])
                        if fas_info:
                            st.markdown("**FAS Standard Summary**")
                            st.info(fas_info["summary"])

                # analysis_result = result
            # for i, result in enumerate(analysis_result["results"]):
            #     with st.expander(f"{i+1}. {result['fas_id']} - {result['name']} (Confidence: {result['confidence']})"):
            #         col1, col2 = st.columns([1, 4])
            #         with col1:
            #             # Use st.badge for confidence level
            #             confidence_color = {
            #                 "High": "green",
            #                 "Medium": "orange",
            #                 "Low": "red"
            #             }.get(result["confidence"], "gray")
            #             st.badge(result["confidence"], color=confidence_color)
            #             st.metric("Match Score", f"{result['score']*100:.1f}%")

            #         with col2:
            #             st.markdown("#### Why this standard applies:")
            #             st.write(result["explanation"])
            #             st.markdown("#### Key aspects of this standard:")
            #             standard_info = FAS_STANDARDS[result["fas_id"]]
            #             st.write(standard_info["summary"])
            #             # Optionally, show matched keywords as colored badges
            #             if "matched_keywords" in result:
            #                 st.markdown(
            #                     " ".join([f":blue-badge[{kw}]" for kw in result["matched_keywords"]]),
            #                     unsafe_allow_html=True
            #                 )

    with tab2:
        st.subheader("AAOIFI Financial Accounting Standards")
        for fas_id, info in FAS_STANDARDS.items():
            with st.expander(f"{fas_id} - {info['name']}"):
                st.write(info["summary"])
                st.write("**Keywords:**", ", ".join(info["keywords"]))

if __name__ == "__main__":
    main()
