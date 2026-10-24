import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.events.consumer import run_view_counter


class Command(BaseCommand):
    help = "Запускает потребителя событий Kafka (подсчёт просмотров)."

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        if not settings.KAFKA_ENABLED:
            self.stderr.write("KAFKA_ENABLED=0: потребителю нечего делать. Проверьте .env")
            return
        try:
            run_view_counter()
        except KeyboardInterrupt:
            self.stdout.write("Остановлен.")
