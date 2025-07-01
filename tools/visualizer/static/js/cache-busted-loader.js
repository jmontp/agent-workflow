/**
 * Cache-Busted Resource Loader
 * Generated: 2025-07-01T00:35:23.621651
 * 
 * This module ensures resources are loaded with proper cache busting
 * and provides fallback mechanisms for failed loads.
 */

class CacheBustedLoader {
    constructor() {
        this.timestamp = Date.now();
        this.cacheKey = Math.random().toString(36).substr(2, 9);
        this.retryAttempts = new Map();
        this.maxRetries = 3;
        
        console.log('🔄 Cache-busted loader initialized:', {
            timestamp: this.timestamp,
            cacheKey: this.cacheKey
        });
    }
    
    /**
     * Load a script with cache busting and retry logic
     */
    async loadScript(src, id = null) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            
            // Add cache busting parameters
            const separator = src.includes('?') ? '&' : '?';
            const cacheBustedSrc = src + separator + 'cb=' + this.timestamp + '&v=' + this.cacheKey;
            
            script.src = cacheBustedSrc;
            if (id) script.id = id;
            
            script.onload = () => {
                console.log('✅ Script loaded successfully:', src);
                resolve(script);
            };
            
            script.onerror = () => {
                console.error('❌ Script failed to load:', src);
                
                // Try retry with different cache buster
                const retryCount = this.retryAttempts.get(src) || 0;
                if (retryCount < this.maxRetries) {
                    this.retryAttempts.set(src, retryCount + 1);
                    console.log(`🔄 Retrying script load (${retryCount + 1}/${this.maxRetries}):`, src);
                    
                    setTimeout(() => {
                        this.loadScript(src, id).then(resolve).catch(reject);
                    }, 1000 * (retryCount + 1)); // Exponential backoff
                } else {
                    reject(new Error(`Failed to load script after ${this.maxRetries} attempts: ${src}`));
                }
            };
            
            document.head.appendChild(script);
        });
    }
    
    /**
     * Load a stylesheet with cache busting
     */
    async loadStylesheet(href, id = null) {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            
            // Add cache busting parameters
            const separator = href.includes('?') ? '&' : '?';
            const cacheBustedHref = href + separator + 'cb=' + this.timestamp + '&v=' + this.cacheKey;
            
            link.href = cacheBustedHref;
            if (id) link.id = id;
            
            link.onload = () => {
                console.log('✅ Stylesheet loaded successfully:', href);
                resolve(link);
            };
            
            link.onerror = () => {
                console.error('❌ Stylesheet failed to load:', href);
                reject(new Error(`Failed to load stylesheet: ${href}`));
            };
            
            document.head.appendChild(link);
        });
    }
    
    /**
     * Verify and reload critical resources if needed
     */
    async verifyCriticalResources() {
        const criticalChecks = [
            { name: 'Socket.IO', check: () => typeof io !== 'undefined' },
            { name: 'Mermaid', check: () => typeof mermaid !== 'undefined' },
            { name: 'ChatComponents', check: () => typeof ChatComponents !== 'undefined' },
            { name: 'DiscordChat', check: () => typeof DiscordChat !== 'undefined' }
        ];
        
        const missing = [];
        for (const { name, check } of criticalChecks) {
            try {
                if (!check()) {
                    missing.push(name);
                }
            } catch (e) {
                missing.push(name);
            }
        }
        
        if (missing.length > 0) {
            console.warn('⚠️ Missing critical resources:', missing);
            
            // Attempt to reload missing resources
            const resourceMap = {
                'Socket.IO': 'https://cdn.socket.io/4.7.2/socket.io.min.js',
                'Mermaid': 'https://cdn.jsdelivr.net/npm/mermaid@10.4.0/dist/mermaid.min.js',
                'ChatComponents': '/static/js/chat-components.js',
                'DiscordChat': '/static/js/discord-chat.js'
            };
            
            for (const resource of missing) {
                if (resourceMap[resource]) {
                    try {
                        await this.loadScript(resourceMap[resource]);
                        console.log(`✅ Reloaded missing resource: ${resource}`);
                    } catch (e) {
                        console.error(`❌ Failed to reload resource: ${resource}`, e);
                    }
                }
            }
        }
        
        return missing.length === 0;
    }
}

// Global instance
window.cacheBustedLoader = new CacheBustedLoader();

// Auto-verify critical resources after DOM load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        window.cacheBustedLoader.verifyCriticalResources();
    }, 1000);
});

console.log('🚀 Cache-busted resource loader ready');
