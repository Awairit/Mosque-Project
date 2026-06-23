"""Shared abstract models.

These are safe foundations for future domain models and do not create database
tables by themselves.
"""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract model that adds created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
