from django.db import migrations

GENERAL_FUND_SLUG = 'general-sadaqah-fund'


def create_general_fund(apps, schema_editor):
    Campaign = apps.get_model('campaigns', 'Campaign')

    if Campaign.objects.filter(slug=GENERAL_FUND_SLUG).exists():
        return  # already exists (e.g. migration re-run) — don't duplicate

    Campaign.objects.create(
        title='সাধারণ সদকা তহবিল',
        title_en='General Sadaqah Fund',
        slug=GENERAL_FUND_SLUG,
        description=(
            'কোনো নির্দিষ্ট ক্যাম্পেইন বেছে না নিয়েই দান করতে চাইলে এখানে দিন। '
            'এই তহবিলের অর্থ সবচেয়ে জরুরি প্রয়োজন অনুযায়ী বিভিন্ন চলমান ক্যাম্পেইনে ব্যবহার করা হয়।'
        ),
        description_en=(
            "Donate here if you don't want to choose one specific campaign. "
            "Funds are directed to whichever ongoing campaign needs it most urgently."
        ),
        short_description='যেকোনো জরুরি প্রয়োজনে ব্যবহারের জন্য সাধারণ দান তহবিল',
        short_description_en='A general fund used wherever the need is most urgent',
        # A high, symbolic target so this permanent/ongoing fund never shows
        # as "100% complete" — Munna can adjust this later from admin if needed.
        target_amount=10000000,
        raised_amount=0,
        status='active',
        is_featured=True,
        # NOTE: same bKash number seen on Munna's other live campaigns — he
        # should double check/update this (and add Nagad/Rocket) from the
        # admin panel after this migration runs.
        bkash_number='01923513404',
    )


def remove_general_fund(apps, schema_editor):
    Campaign = apps.get_model('campaigns', 'Campaign')
    Campaign.objects.filter(slug=GENERAL_FUND_SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0007_comment_user'),
    ]

    operations = [
        migrations.RunPython(create_general_fund, remove_general_fund),
    ]
