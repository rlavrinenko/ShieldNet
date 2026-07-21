export interface GuildModule {
  module_key: string;
  name: string;
  description: string | null;
  icon: string | null;
  version: string;
  is_core: boolean;
  enabled: boolean;
  configuration: Record<string, unknown>;
  revision: number;
}

export interface GuildModuleUpdate extends GuildModule {
  guild_id: string;
  sync_required: boolean;
}
