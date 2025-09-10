<?php

namespace pompom\craftmeditransfermailer\models;

use Craft;
use craft\base\Model;
use craft\behaviors\EnvAttributeParserBehavior;

/**
 * MediTransfer Mailer settings
 */
class Settings extends Model
{
    public string $postmarkApiToken = '';
    public string $postmarkServerToken = '';
    public string $fromEmail = '';
    public string $fromName = 'MediTransfer';
    public string $replyToEmail = '';
    public string $webhookSecret = '';
    public bool $enableTracking = true;
    public int $batchSize = 100;
    public bool $testMode = false;
    
    public function defineRules(): array
    {
        return [
            [['postmarkApiToken', 'postmarkServerToken', 'fromEmail'], 'required'],
            [['fromEmail', 'replyToEmail'], 'email'],
            [['batchSize'], 'integer', 'min' => 10, 'max' => 500],
            [['enableTracking', 'testMode'], 'boolean'],
            [['fromName', 'webhookSecret'], 'string'],
        ];
    }
    
    public function behaviors(): array
    {
        return [
            'parser' => [
                'class' => EnvAttributeParserBehavior::class,
                'attributes' => ['postmarkApiToken', 'postmarkServerToken', 'fromEmail', 'replyToEmail'],
            ],
        ];
    }
}
