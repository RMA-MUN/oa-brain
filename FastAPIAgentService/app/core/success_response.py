from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def success_response(message: str = "success", data = None) -> JSONResponse:
    """
    成功响应体
    :param message: 响应消息
    :param data: 响应数据
    :return: JSONResponse
    """
    response = {
        "code": 200,
        "message": message,
        "data": data
    }
    return JSONResponse(content=jsonable_encoder(response))