<?php

namespace pompom\craftmeditransfermailer\records;

use craft\db\ActiveRecord;

/**
 * @property int $id
 * @property int $campaignId
 * @property int $recipientId
 * @property string|null $messageId
 * @property string $event
 * @property string|null $eventData
 * @property string|null $ipAddress
 * @property string|null $userAgent
 * @property string|null $clickedUrl
 * @property string $timestamp
 * @property string $dateCreated
 * @property string $uid
 */
class EmailTrackingRecord extends ActiveRecord
{
    public static function tableName(): string
    {
        return '{{%meditransfer_tracking}}';
    }
}