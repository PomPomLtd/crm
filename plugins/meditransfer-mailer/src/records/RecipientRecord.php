<?php

namespace pompom\craftmeditransfermailer\records;

use craft\db\ActiveRecord;
use craft\records\Element;
use yii\db\ActiveQuery;

/**
 * @property int $id
 * @property int $campaignId
 * @property int|null $elementId
 * @property string $email
 * @property string|null $name
 * @property string|null $organizationName
 * @property string|null $organizationType
 * @property string|null $customData
 * @property string $status
 * @property string|null $postmarkMessageId
 * @property string|null $sentDate
 * @property string|null $openedDate
 * @property string|null $clickedDate
 * @property string|null $bouncedDate
 * @property string|null $errorMessage
 * @property string $dateCreated
 * @property string $dateUpdated
 * @property string $uid
 */
class RecipientRecord extends ActiveRecord
{
    public static function tableName(): string
    {
        return '{{%meditransfer_recipients}}';
    }
    
    public function getCampaign(): ActiveQuery
    {
        return $this->hasOne(CampaignRecord::class, ['id' => 'campaignId']);
    }
    
    public function getElement(): ActiveQuery
    {
        return $this->hasOne(Element::class, ['id' => 'elementId']);
    }
    
    public function getTracking(): ActiveQuery
    {
        return $this->hasMany(EmailTrackingRecord::class, ['recipientId' => 'id']);
    }
}