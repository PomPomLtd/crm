<?php

namespace pompom\craftmeditransfermailer\records;

use craft\db\ActiveRecord;

/**
 * @property int $id
 * @property string $name
 * @property string $handle
 * @property string $subject
 * @property string|null $htmlContent
 * @property string|null $textContent
 * @property string|null $variables
 * @property string|null $preheaderText
 * @property bool $isActive
 * @property string $dateCreated
 * @property string $dateUpdated
 * @property string $uid
 */
class EmailTemplateRecord extends ActiveRecord
{
    public static function tableName(): string
    {
        return '{{%meditransfer_templates}}';
    }
}