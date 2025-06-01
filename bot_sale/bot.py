from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    FileSearchTool,
    trace,
    function_tool
)
import asyncio
from pydantic import BaseModel
import pandas as pd
from thefuzz import process
import os

# Thiết lập API Key
os.environ["OPENAI_API_KEY"] = '###'

llm = "gpt-4o-mini" #o3-mini 

file_path = 'products.csv' 
df_product = pd.read_csv(file_path)

@function_tool
async def ProductSearch(product_name: str) -> str:
    """Trả lời những câu hỏi liên quan đến tìm kiếm thông tin về một sản phẩm cụ thể của công công ty.
        Ví du:
        -Thông tin chi tiết về MacBook Pro 16-inch
        - Samsung Galaxy A52
        - thông tin Dell Inspiron 15
        - điện thoại iPhone 12
    Args:
        product_name: tên sản phẩm cụ thể cần lấy thông tin
    """
    product_list = df_product['name'].tolist()
    list_product_name_by_fuzzy = process.extract(product_name, product_list, limit=3) # [(str, int)]
    
    result_str = f"Một số sản phẩm liên quan đến {product_name} gồm: \n"
    for index, product_name_by_fuzzy in enumerate(list_product_name_by_fuzzy):
        product_name_by_fuzzy = product_name_by_fuzzy[0]
        product_info = df_product[df_product['name'] == product_name_by_fuzzy]
        if not product_info.empty:
            name = product_info.iloc[0]['name']
            price = product_info.iloc[0]['price']
            description = product_info.iloc[0]['description']
            url = product_info.iloc[0]['url']
            result_str += f"{index+1}- Sản phẩm: {name}, Giá: {price}, Mô tả: {description}, Link sản phẩm: {url} \n"
    
    return result_str

class other_agency(BaseModel):
    reasoning: str
    block: bool

guardrail_agent = Agent(
    name="Guardrail check",
    model = llm,
    instructions="Bạn chỉ kiểm tra thông tin của câu hỏi có liên quan đến thông tin, sản phẩm của cửa hàng khác TechLife (hỏi về cửa hàng khác trả về True) (Ví dụ hỏi về 1 loại sản phẩm của cửa hàng Thế Giới Di Động, FPT Shop,...), các câu hỏi không liên quan gì đến cửa hàng khác trả về False. Và luôn nhớ TechLife là tên cửa hàng không phải một hãng sản xuất nên các câu hỏi có chứa tên hãng hoặc tên chi tiết của sản phẩm (ví dụ hỏi về sản phẩm của hãng Apple, Dell, SamSung,..., hỏi thông tin chi tiết về iPhone 13 Pro, Samsung Galaxy A52, Dell Latitude 7420,... ) thì câu đó là hỏi về cửa hàng TechLife vì vậy các câu này cần trả về False",
    output_type=other_agency
)

@input_guardrail
async def other_agency_guardrail(
    context: RunContextWrapper[None], agen: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """Đây là một input guardrail function, được chạy khi gọi một agent kiểm tra thông tin 
    câu hỏi có phải về công ty, cửa hàng khác, không phải là công ty, cửa hàng của chúng tôi (công ty tôi là TechLife)
    """

    result = await Runner.run(guardrail_agent, input, context=context.context)
    final_output = result.final_output_as(other_agency)

    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=final_output.block,
    )

manager_bot = Agent(
    name = 'Bot-sale',
    instructions = ("""
        Bạn là một nhân viên chăm sóc khách hàng chuyên nghiệp và thân thiện của công ty TechLife. Nhiệm vụ của bạn là hỗ trợ khách hàng bằng cách lắng nghe thắc mắc, giải đáp câu hỏi, và tư vấn sản phẩm với giọng điệu vui tươi, lịch sự, dễ thương.
        - Tuyệt đối không được bịa đặt thông tin, sử dụng ngôn ngữ không phù hợp, hoặc thô lỗ.
        - Bạn hãy xưng hô anh hoặc chị dựa theo cuộc trò chuyện với khách hàng.
        - Sử dụng từ ngữ như “dạ, vâng” trong câu trả lời để thể hiện sự chuyên nghiệp.

        Bạn cần thực hiện lần lượt các hành động sau nếu nhận được câu hỏi về muốn mua loại sản phẩm nào đó:          
        1. Khi nhận câu hỏi về muốn mua loại sản phẩm nào đó thì cần hỏi tên khách hàng.
        2. Khi nhận được tên khách hàng bạn cần hỏi tuổi của khách hàng.
        3. Khi nhận được tuổi khách hàng bạn cần hỏi giới tính của khách hàng.
                    
        Sử dụng tool FileSearchTool khi nhận câu hỏi về thông tin của cửa hàng, không dùng khi nhận câu hỏi chi tiết có tên của 1 sản phẩm chính xác nào đó (ví dụ: sẽ không dùng tool này khi gặp các câu hỏi cụ thể có chứa iPhone 13 Pro, Samsung Galaxy S21, MacBook Air M1, Dell XPS 13,...) 
        Sử dụng tool ProductSearch khi nhận câu hỏi thông tin chi tiết về 1 sản phẩm có tên rõ ràng nào đó (ví dụ: iPhone 13 Pro, Samsung Galaxy S21, MacBook Air M1, Dell XPS 13,...)    
        Khi tư vấn thông tin sản phẩm chi tiết bạn phải luôn đưa url của sản phẩm từ của hàng của chúng tôi!!!
                    
        Bạn phải luôn chủ động xin số điện thoại của khách hàng khi khách hàng muốn tìm hiểu thông tin sản phẩm cụ thể hoặc đặt mua sản phẩm của công ty.

        Khi bạn nhận được số điện thoại từ câu chat của người dùng thì bạn phải luôn thêm vào câu trả lời:"Em đã ghi nhận số điện thoại và phòng kinh doanh sẽ liên hệ lại anh/chị sau"
                    
    """
    ),
    model = llm,
    input_guardrails = [other_agency_guardrail],
    tools = [
        ProductSearch, 
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=["vs_67fdabd712148191a85838e6b1a872c9"],
            include_search_results=True
        ),
    ],
)

async def get_reponse(request):
    try:
        with trace("Chatbot Sale TechLife"):
            result = await Runner.run(manager_bot, request)

            final_output = result.final_output if hasattr (result, 'final_output') else None
            new_items = [str(out) for out in result.new_items] if hasattr(result, 'new_items') else []
            return{
                "final_output": final_output,
                "new_items": new_items
        }
    except InputGuardrailTripwireTriggered:
        return{
            "final_output": "Xin lỗi, em chỉ có thông tin tư vấn về cửa hàng TechLife. Anh/Chị có cần em hỗ trợ về thông tin sản phẩm của cửa hàng không ạ"
        }

# with trace("Chat bot sale"):
#     while True:
#         user_request = input("Nhập request:")
#         result = asyncio.run(get_reponse(user_request))

#         if user_request.lower() == 'exit':
#             print("Đã thoát khỏi chương trình.")
#             break

#         if result['final_output'] :
#             print(result['final_output'])
