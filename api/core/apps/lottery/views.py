import logging
import random

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import BetSerializer
from .scraper import get_lottery_result

logger = logging.getLogger(__name__)


class LotteryResultView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            result = get_lottery_result()
            return Response({"result": result}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(f"Get Resultado da Mega Sena - {str(ex)}")
            return Response({"error": "Tivemos um problema para realizar a requisição."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BetView(APIView):

    def get(self, request, *args, **kwargs):
        bets = request.user.bets
        serializer = BetSerializer(bets, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        payload = request.data.copy()

        try:
            dozens = int(request.data.get("dozens"))
        except ValueError as ex:
            logger.error(f"POST Bet - {str(ex)}")
            return Response({"erro": "O número de dezenas deve ser do tipo Inteiro."},
                            status=status.HTTP_400_BAD_REQUEST)

        if not (6 <= dozens <= 10):
            return Response({"erro": "O número de dezenas deve ser no mínimo 6 e no máximo 10."},
                            status=status.HTTP_400_BAD_REQUEST)

        numbers = sorted(list(random.sample(range(1, 61), dozens)))

        payload.update({
            "user": request.user.pk,
            "numbers": numbers
        })

        serializer = BetSerializer(data=payload)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BetResultView(APIView):
    def get(self, request, *args, **kwargs):
        try:

            bet = request.user.bets.all().first()

            if not bet:
                return Response({"erro": "Você ainda não fez nenhuma aposta."},
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = BetSerializer(bet)

            result = get_lottery_result()
            numbers = serializer.data.get("numbers")
            right_numbers = sorted(list(set(numbers) & set(result)))

            response = {
                "right_numbers": {
                    "total_right": len(right_numbers),
                    "numbers": right_numbers
                },
                "numbers": numbers,
                "result": result
            }

            return Response(response)
        except Exception as ex:
            logger.error(f"Get Resultado da Última Aposta - {str(ex)}")
            return Response({"error": "Tivemos um problema para realizar a requisição."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
