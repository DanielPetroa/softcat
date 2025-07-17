from django.db import models
from geometries.models import Geometria

class PayoutOption(models.Model):
    TRIGGER_TYPE_CHOICES = [
        ('threshold', 'Threshold'),
        ('index', 'Index'),
        ('parametric', 'Parametric'),
        ('cumulative', 'Cumulative'),
        ('binary', 'Binary'),
    ]
    
    FILTER_CONDITION_CHOICES = [
        ('>=', 'Greater than or equal'),
        ('<=', 'Less than or equal'),
        ('==', 'Equal to'),
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('!=', 'Not equal to'),
    ]
    
    PAYOUT_METHOD_CHOICES = [
        ('area_based', 'Area Based'),
        ('fixed', 'Fixed Amount'),
        ('scaled', 'Scaled'),
        ('percentage', 'Percentage'),
        ('tiered', 'Tiered'),
    ]

    id_payout_option = models.AutoField(primary_key=True)
    id_geometria = models.ForeignKey(
        Geometria, 
        on_delete=models.CASCADE,
        related_name='payout_options',
        verbose_name='Geometry'
    )
    
    # Trigger Configuration
    trigger_type = models.CharField(
        max_length=100, 
        choices=TRIGGER_TYPE_CHOICES,
        verbose_name='Trigger Type',
        help_text='Type of trigger mechanism for payout'
    )
    int_var = models.CharField(
        max_length=100,
        verbose_name='Variable',
        help_text='Variable to monitor (e.g., wind_speed, precipitation, magnitude)'
    )
    int_val1 = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name='Threshold Value 1',
        help_text='Primary threshold value for trigger'
    )
    int_val2 = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='Threshold Value 2',
        help_text='Secondary threshold value (optional)'
    )
    
    # Filter Configuration
    filter_var = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Filter Variable',
        help_text='Additional variable for filtering (optional)'
    )
    filter_value = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Filter Value',
        help_text='Value for filter condition'
    )
    filter_condition = models.CharField(
        max_length=50, 
        choices=FILTER_CONDITION_CHOICES,
        blank=True,
        verbose_name='Filter Condition',
        help_text='Condition for filter evaluation'
    )
    
    # Payout Configuration
    payout_percent_limit1 = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Payout Percentage 1 (%)',
        help_text='Percentage of limit for first tier (0-100)'
    )
    payout_percent_limit2 = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='Payout Percentage 2 (%)',
        help_text='Percentage of limit for second tier (optional)'
    )
    payout_method_by_geom = models.CharField(
        max_length=100,
        choices=PAYOUT_METHOD_CHOICES,
        verbose_name='Payout Method',
        help_text='Method for calculating payout based on geometry'
    )
    
    # Status
    activo = models.BooleanField(
        default=True,
        verbose_name='Active',
        help_text='Whether this payout option is active'
    )
    creado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    class Meta:
        db_table = 'payout_options'
        verbose_name = 'Payout Option'
        verbose_name_plural = 'Payout Options'
        ordering = ['-creado_en']

    def __str__(self):
        return f"Payout {self.id_payout_option} - {self.id_geometria.nombre} ({self.trigger_type})"

    @property
    def has_secondary_threshold(self):
        """Check if this payout has a secondary threshold configured"""
        return self.int_val2 is not None

    @property
    def has_filter(self):
        """Check if this payout has filter configuration"""
        return bool(self.filter_var and self.filter_value and self.filter_condition)

    @property
    def total_payout_percentage(self):
        """Calculate total payout percentage"""
        total = self.payout_percent_limit1
        if self.payout_percent_limit2:
            total += self.payout_percent_limit2
        return total

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError
        
        # Validate payout percentages
        if self.payout_percent_limit1 < 0 or self.payout_percent_limit1 > 100:
            raise ValidationError({'payout_percent_limit1': 'Percentage must be between 0 and 100'})
        
        if self.payout_percent_limit2 and (self.payout_percent_limit2 < 0 or self.payout_percent_limit2 > 100):
            raise ValidationError({'payout_percent_limit2': 'Percentage must be between 0 and 100'})
        
        # Validate total doesn't exceed 100%
        if self.total_payout_percentage > 100:
            raise ValidationError('Total payout percentage cannot exceed 100%')
        
        # Validate filter consistency
        if any([self.filter_var, self.filter_value, self.filter_condition]):
            if not all([self.filter_var, self.filter_value, self.filter_condition]):
                raise ValidationError('All filter fields must be provided if using filters')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)