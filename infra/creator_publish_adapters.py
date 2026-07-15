"""PublishAdapter protocol and per-platform stubs for creator publish flow."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from infra.studio_registry import StudioProject


@dataclass(frozen=True)
class PublishCapabilities:
    supports_submission_pack: bool = True
    supports_full_book: bool = False
    oauth_required: bool = True
    max_intro_chars: int = 2000


@dataclass
class PublishSubmitResult:
    status: str
    message: str
    adapter_id: str
    connection: str = "stub"
    external_url: str | None = None
    package_hint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PublishAdapter(Protocol):
    """统一发布适配器协议（各平台实现可替换）。"""

    platform_id: str
    label: str

    def capabilities(self) -> PublishCapabilities: ...

    def connection_status(self, project: StudioProject) -> str: ...

    def submit(
        self,
        project: StudioProject,
        *,
        include_outline: bool,
        intro: str,
        mode: str,
    ) -> PublishSubmitResult: ...


class _BaseStubAdapter:
    platform_id: str = "custom"
    label: str = "自定义平台"

    def capabilities(self) -> PublishCapabilities:
        return PublishCapabilities()

    def connection_status(self, project: StudioProject) -> str:
        _ = project
        return "stub"

    def submit(
        self,
        project: StudioProject,
        *,
        include_outline: bool,
        intro: str,
        mode: str,
    ) -> PublishSubmitResult:
        outline_note = "含大纲节选" if include_outline else "不含大纲"
        return PublishSubmitResult(
            status="adapter_stub",
            message=(
                f"「{self.label}」适配器为占位实现：已校验投稿包（{mode}，{outline_note}）。"
                "接入 OAuth 后将自动上传至平台。"
            ),
            adapter_id=self.platform_id,
            connection=self.connection_status(project),
            package_hint=f"projects/{project.slug}/export/{mode}",
            metadata={"intro_len": len(intro.strip()), "mode": mode},
        )


class FanqiePublishAdapter(_BaseStubAdapter):
    platform_id = "fanqie"
    label = "番茄小说"

    def capabilities(self) -> PublishCapabilities:
        return PublishCapabilities(max_intro_chars=500)


class QidianPublishAdapter(_BaseStubAdapter):
    platform_id = "qidian"
    label = "起点中文网"

    def capabilities(self) -> PublishCapabilities:
        return PublishCapabilities(supports_full_book=True)


class JjwxcPublishAdapter(_BaseStubAdapter):
    platform_id = "jjwxc"
    label = "晋江文学城"


class CustomPublishAdapter(_BaseStubAdapter):
    platform_id = "custom"
    label = "自定义平台"

    def connection_status(self, project: StudioProject) -> str:
        _ = project
        return "disconnected"

    def submit(
        self,
        project: StudioProject,
        *,
        include_outline: bool,
        intro: str,
        mode: str,
    ) -> PublishSubmitResult:
        result = super().submit(
            project,
            include_outline=include_outline,
            intro=intro,
            mode=mode,
        )
        result.status = "queued"
        result.message = "已入队：请使用导出投稿包后手动上传至目标平台。"
        return result


_ADAPTERS: dict[str, PublishAdapter] = {
    FanqiePublishAdapter.platform_id: FanqiePublishAdapter(),
    QidianPublishAdapter.platform_id: QidianPublishAdapter(),
    JjwxcPublishAdapter.platform_id: JjwxcPublishAdapter(),
    CustomPublishAdapter.platform_id: CustomPublishAdapter(),
}


def get_publish_adapter(platform_id: str) -> PublishAdapter:
    return _ADAPTERS.get(platform_id, CustomPublishAdapter())


def list_publish_platforms(project: StudioProject) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for adapter in _ADAPTERS.values():
        caps = adapter.capabilities()
        rows.append(
            {
                "id": adapter.platform_id,
                "label": adapter.label,
                "connection": adapter.connection_status(project),
                "capabilities": {
                    "supports_submission_pack": caps.supports_submission_pack,
                    "supports_full_book": caps.supports_full_book,
                    "oauth_required": caps.oauth_required,
                    "max_intro_chars": caps.max_intro_chars,
                },
            },
        )
    return rows
