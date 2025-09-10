<?php

namespace pompom\craftmeditransfermailer\records;

use craft\db\ActiveRecord;

/**
 * @property int $id
 * @property int $campaignId
 * @property int|null $sectionId
 * @property int|null $entryTypeId
 * @property string|null $fieldConditions
 * @property string $dateCreated
 * @property string $dateUpdated
 * @property string $uid
 */
class CampaignSegmentRecord extends ActiveRecord
{
    public static function tableName(): string
    {
        return '{{%meditransfer_campaign_segments}}';
    }
}