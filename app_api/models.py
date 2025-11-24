from django.db import models


class GiftLink(models.Model):
    """
    Модель для хранения ссылки на подарок
    """
    title = models.CharField(max_length=255, verbose_name="Название", default="Ссылка для подарка")
    url = models.URLField(verbose_name="Ссылка для подарка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Ссылка для подарка"
        verbose_name_plural = "Ссылки для подарка"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
