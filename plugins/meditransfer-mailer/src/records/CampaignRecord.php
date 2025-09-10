<?php

namespace pompom\craftmeditransfermailer\records;

use craft\db\ActiveRecord;
use craft\records\Element;
use yii\db\ActiveQuery;

/**
 * @property int $id
 * @property string $name
 * @property string $subject
 * @property int|null $templateId
 * @property string|null $fromEmail
 * @property string|null $fromName
 * @property string|null $replyToEmail
 * @property string $status
 * @property string|null $scheduledDate
 * @property string|null $completedDate
 * @property int $sentCount
 * @property int $totalRecipients
 * @property int $openedCount
 * @property int $clickedCount
 * @property int $bouncedCount
 * @property string|null $settings
 * @property string $dateCreated
 * @property string $dateUpdated
 * @property string $uid
 */
class CampaignRecord extends ActiveRecord
{
    public static function tableName(): string
    {
        return '{{%meditransfer_campaigns}}';
    }
    
    public function getTemplate(): ActiveQuery
    {
        return $this->hasOne(EmailTemplateRecord::class, ['id' => 'templateId']);
    }
    
    public function getRecipients(): ActiveQuery
    {
        return $this->hasMany(RecipientRecord::class, ['campaignId' => 'id']);
    }
    
    public function getTracking(): ActiveQuery
    {
        return $this->hasMany(EmailTrackingRecord::class, ['campaignId' => 'id']);
    }
    
    public function getSegments(): ActiveQuery
    {
        return $this->hasMany(CampaignSegmentRecord::class, ['campaignId' => 'id']);
    }
}